FROM mcr.microsoft.com/devcontainers/base:ubuntu

ARG USERNAME=kawanos

# 1. ユーザーの調整 (kawanos の作成)
RUN if id -u vscode >/dev/null 2>&1; then \
        usermod -l ${USERNAME} vscode && \
        groupmod -n ${USERNAME} vscode && \
        usermod -d /home/${USERNAME} -m ${USERNAME}; \
    else \
        useradd -m -s /bin/bash ${USERNAME}; \
    fi \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}

# 2. 基本パッケージ、Python3.12、Node.js(npm)、gcloud、Docker CLI のインストール
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y curl wget apt-transport-https ca-certificates gnupg software-properties-common bash-completion \
    # Python 3.12 リポジトリ追加
    && add-apt-repository -y ppa:deadsnakes/ppa \
    # Node.js 20 (npm同梱) リポジトリ追加
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    # Google Cloud CLI リポジトリ追加
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    # aptパッケージの一括インストール
    && apt-get update && apt-get install -y \
       python3.12 python3.12-venv python3.12-dev \
       nodejs \
       vim \
       tmux \
       google-cloud-cli \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. kubectl と kubectx / kubens / stern のインストール
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl && mv kubectl /usr/local/bin/ \
    && git clone https://github.com/ahmetb/kubectx.git /opt/kubectx \
    && ln -s /opt/kubectx/kubectx /usr/local/bin/kubectx \
    && ln -s /opt/kubectx/kubens /usr/local/bin/kubens \
    && curl -Lo stern.tar.gz https://github.com/stern/stern/releases/download/v1.33.1/stern_1.33.1_linux_amd64.tar.gz \
    && tar xzf stern.tar.gz stern \
    && chmod +x stern && mv stern /usr/local/bin/ \
    && rm stern.tar.gz

# 4. Terraform のインストール
RUN wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
    && (type -p wget >/dev/null || (apt-get update && apt-get install wget -y)) \
    && apt-get update && apt-get install -y terraform \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. npm 経由で gemini-cli と claude-code をインストール
RUN npm install -g @google/gemini-cli @anthropic-ai/claude-code firebase-tools

# ==========================================
# 以降は kawanos ユーザーとしての処理
# ==========================================
USER ${USERNAME}
ENV HOME="/home/${USERNAME}"

# 6. uv のインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="${HOME}/.local/bin:${PATH}"

# 7. .bashrc-params のコピー
# ※注意: ビルド前にホスト側の .bashrc-params を .devcontainer フォルダ内に配置しておく必要があります
COPY --chown=${USERNAME}:${USERNAME} .bashrc ${HOME}/.bashrc

# COPY --chown=${USERNAME}:${USERNAME} .gitconfig ${HOME}/.gitconfig
# COPY --chown=${USERNAME}:${USERNAME} .tmux.conf ${HOME}/.tmux.conf

# 8. 各種 completion (自動補完) と .bashrc-params の読み込み設定を .bashrc に追記
RUN cat << 'EOF' >> ${HOME}/.bashrc

# Load .bashrc-params
if [ -f ~/.bashrc-params ]; then
    source ~/.bashrc-params
fi

# Load global bash_completion
if [ -f /etc/bash_completion ]; then
    source /etc/bash_completion
fi

# uv completion
eval "$(uv generate-shell-completion bash)"

# kubectl completion
source <(kubectl completion bash)
alias k=kubectl
complete -o default -F __start_kubectl k

# kubectx / kubens completion
export PATH=/opt/kubectx:$PATH
source /opt/kubectx/completion/kubectx.bash
source /opt/kubectx/completion/kubens.bash

# npm completion
source <(npm completion)

# firebase completion
source <(firebase completion)

# stern completion
source <(stern completion bash)

# gcloud completion
if [ -f /usr/share/google-cloud-sdk/completion.bash.inc ]; then
    source /usr/share/google-cloud-sdk/completion.bash.inc
fi

# Terraform completion
complete -C /usr/bin/terraform terraform

# gh completion
eval "$(gh completion -s bash)"
EOF
