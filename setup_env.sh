#!/bin/bash

# CashUp项目环境配置脚本

echo "=== CashUp 项目环境配置 ==="

# 检查并配置nvm环境变量
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    echo "配置nvm环境变量..."
    
    # 添加到.zshrc
    if ! grep -q "export NVM_DIR" ~/.zshrc; then
        echo '' >> ~/.zshrc
        echo '# NVM configuration' >> ~/.zshrc
        echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.zshrc
        echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.zshrc
        echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.zshrc
        echo "已添加nvm配置到 ~/.zshrc"
    else
        echo "nvm配置已存在于 ~/.zshrc"
    fi
    
    # 添加到.bash_profile
    if [ -f ~/.bash_profile ] && ! grep -q "export NVM_DIR" ~/.bash_profile; then
        echo '' >> ~/.bash_profile
        echo '# NVM configuration' >> ~/.bash_profile
        echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bash_profile
        echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bash_profile
        echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.bash_profile
        echo "已添加nvm配置到 ~/.bash_profile"
    fi
else
    echo "警告: nvm未安装或配置不正确"
fi

# 检查uv环境变量
if [ -f "$HOME/.local/bin/uv" ]; then
    echo "配置uv环境变量..."
    
    # 添加到.zshrc
    if ! grep -q "/.local/bin" ~/.zshrc; then
        echo '' >> ~/.zshrc
        echo '# UV configuration' >> ~/.zshrc
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo "已添加uv配置到 ~/.zshrc"
    else
        echo "uv配置已存在于 ~/.zshrc"
    fi
else
    echo "警告: uv未安装或配置不正确"
fi

# 激活cashup虚拟环境
if [ -d "cashup" ]; then
    echo "激活cashup虚拟环境..."
    source cashup/bin/activate
    echo "虚拟环境已激活: $(which python)"
else
    echo "警告: cashup虚拟环境不存在"
fi

echo "=== 环境配置完成 ==="
echo "请运行 'source ~/.zshrc' 或重新打开终端以使配置生效"