import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from google.cloud import discoveryengine_v1 as discoveryengine


@dataclass
class Citation:
    title: str
    uri: str


@dataclass
class SearchResult:
    summary: str
    citations: list[Citation]


@dataclass
class SummaryConfig:
    preamble: str = ""
    result_count: int = 5
    include_citations: bool = True


def load_prompt_config() -> SummaryConfig:
    config_path = Path(__file__).parent.parent.parent / "config" / "prompts.yaml"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
            summary = config.get("summary", {})
            return SummaryConfig(
                preamble=summary.get("preamble", ""),
                result_count=summary.get("result_count", 5),
                include_citations=summary.get("include_citations", True),
            )
    return SummaryConfig()


class SearchService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("VERTEX_AI_SEARCH_LOCATION", "global")
        self.datastore_id = os.getenv("VERTEX_AI_SEARCH_DATASTORE_ID")
        self.summary_config = load_prompt_config()
        self.conversation_ids: dict[str, str] = {}

        if self.project_id and self.datastore_id:
            self.client = discoveryengine.ConversationalSearchServiceClient()
            self.datastore_path = self.client.data_store_path(
                project=self.project_id,
                location=self.location,
                data_store=self.datastore_id,
            )
        else:
            self.client = None
            self.datastore_path = None

    async def search(
        self, query: str, session_id: str, history: list[dict] | None = None
    ) -> SearchResult:
        if not self.client:
            return self._mock_response(query, history)

        try:
            conversation_id = self.conversation_ids.get(session_id)

            # 会話履歴からメッセージを構築
            messages = self._build_conversation_messages(history or [])
            conversation = discoveryengine.Conversation(messages=messages)

            # 要約設定（システムプロンプト）
            summary_spec = discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=self.summary_config.result_count,
                include_citations=self.summary_config.include_citations,
                model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                    preamble=self.summary_config.preamble,
                ),
            )

            if conversation_id:
                conversation_name = self.client.conversation_path(
                    project=self.project_id,
                    location=self.location,
                    data_store=self.datastore_id,
                    conversation=conversation_id,
                )
                request = discoveryengine.ConverseConversationRequest(
                    name=conversation_name,
                    query=discoveryengine.TextInput(input=query),
                    serving_config=f"{self.datastore_path}/servingConfigs/default_serving_config",
                    conversation=conversation,
                    summary_spec=summary_spec,
                )
            else:
                request = discoveryengine.ConverseConversationRequest(
                    name=f"{self.datastore_path}/conversations/-",
                    query=discoveryengine.TextInput(input=query),
                    serving_config=f"{self.datastore_path}/servingConfigs/default_serving_config",
                    conversation=conversation,
                    summary_spec=summary_spec,
                )

            response = self.client.converse_conversation(request)

            if not conversation_id and response.conversation:
                conv_name = response.conversation.name
                self.conversation_ids[session_id] = conv_name.split("/")[-1]

            summary = ""
            citations: list[Citation] = []

            if response.reply.summary:
                summary = response.reply.summary.summary_text
                citations = self._extract_citations(response)
            else:
                summary = response.reply.reply

            return SearchResult(summary=summary, citations=citations)

        except Exception as e:
            return SearchResult(summary=f"Error: {e}", citations=[])

    def clear_session(self, session_id: str) -> None:
        if session_id in self.conversation_ids:
            del self.conversation_ids[session_id]

    def _build_conversation_messages(
        self, history: list[dict]
    ) -> list[discoveryengine.ConversationMessage]:
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(
                    discoveryengine.ConversationMessage(
                        user_input=discoveryengine.TextInput(input=msg["content"])
                    )
                )
            elif msg["role"] == "assistant":
                messages.append(
                    discoveryengine.ConversationMessage(
                        reply=discoveryengine.Reply(reply=msg["content"])
                    )
                )
        return messages

    def _convert_gs_to_https(self, uri: str) -> str:
        if uri.startswith("gs://"):
            # gs://bucket-name/path -> https://storage.googleapis.com/bucket-name/path
            return uri.replace("gs://", "https://storage.googleapis.com/", 1)
        return uri

    def _extract_citations(self, response) -> list[Citation]:
        citations: list[Citation] = []
        seen_uris: set[str] = set()

        # 1. summary.references から取得
        summary = response.reply.summary
        if hasattr(summary, "references") and summary.references:
            for ref in summary.references:
                uri = getattr(ref, "uri", "") or ""
                title = getattr(ref, "title", "") or ""

                # uri が空の場合、document フィールドから取得を試みる
                if not uri and hasattr(ref, "document"):
                    doc = ref.document
                    if hasattr(doc, "derived_struct_data"):
                        struct_data = doc.derived_struct_data
                        uri = struct_data.get("link", "") or struct_data.get("uri", "")
                        if not title:
                            title = struct_data.get("title", "")

                if uri:
                    uri = self._convert_gs_to_https(uri)
                    if uri not in seen_uris:
                        seen_uris.add(uri)
                        citations.append(Citation(title=title or uri, uri=uri))

        # 2. summary_with_metadata.citation_metadata から取得
        if hasattr(summary, "summary_with_metadata"):
            metadata = summary.summary_with_metadata
            if hasattr(metadata, "citation_metadata") and metadata.citation_metadata:
                for citation in metadata.citation_metadata.citations:
                    for source in getattr(citation, "sources", []):
                        uri = getattr(source, "uri", "") or ""
                        title = ""
                        if hasattr(source, "reference_id"):
                            # reference_id を使って references から情報を取得
                            ref_id = source.reference_id
                            if hasattr(metadata, "references") and ref_id < len(metadata.references):
                                ref = metadata.references[ref_id]
                                uri = getattr(ref, "uri", "") or uri
                                title = getattr(ref, "title", "") or ""
                        if uri:
                            uri = self._convert_gs_to_https(uri)
                            if uri not in seen_uris:
                                seen_uris.add(uri)
                                citations.append(Citation(title=title or uri, uri=uri))

        # 3. search_results から取得（上記で取得できなかった場合）
        if not citations and hasattr(response, "search_results"):
            for result in response.search_results:
                doc = result.document
                uri = ""
                title = ""

                if hasattr(doc, "derived_struct_data"):
                    struct_data = doc.derived_struct_data
                    uri = struct_data.get("link", "") or struct_data.get("uri", "")
                    title = struct_data.get("title", "")

                if not uri and hasattr(doc, "struct_data"):
                    struct_data = doc.struct_data
                    uri = struct_data.get("link", "") or struct_data.get("uri", "")
                    title = struct_data.get("title", "")

                if uri:
                    uri = self._convert_gs_to_https(uri)
                    if uri not in seen_uris:
                        seen_uris.add(uri)
                        citations.append(Citation(title=title or uri, uri=uri))

        return citations

    def _mock_response(self, query: str, history: list[dict] | None = None) -> SearchResult:
        history_context = ""
        if history:
            history_context = f" (会話履歴: {len(history)}件のメッセージ)"

        return SearchResult(
            summary=f"[Mock Response] You asked: '{query}'.{history_context} Configure GOOGLE_CLOUD_PROJECT and VERTEX_AI_SEARCH_DATASTORE_ID to use Vertex AI Search.",
            citations=[
                Citation(title="Example Document 1", uri="https://example.com/doc1"),
                Citation(title="Example Document 2", uri="https://example.com/doc2"),
            ],
        )
