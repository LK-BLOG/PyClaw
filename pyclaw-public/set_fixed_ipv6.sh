#!/bin/bash
# PyClaw 固定 IPv6 地址配置脚本
# 给电脑加一个固定的 IPv6 地址，重启后自动恢复

INTERFACE="wlp13s0"
PREFIX=$(ip -6 addr show scope global | grep -oP '2409:8a30:b4a1:86a4:\w+' | head -1 | cut -d: -f1-5)
FIXED_SUFFIX="dead:beef:cafe:2469"

if [ -z "$PREFIX" ]; then
    echo "❌ 无法获取 IPv6 前缀，请检查网络连接"
    exit 1
fi

FIXED_IP="${PREFIX}::${FIXED_SUFFIX}/64"

echo "🦞 PyClaw 固定 IPv6 地址配置"
echo "=============================="
echo "接口:     $INTERFACE"
echo "固定地址: $FIXED_IP"
echo "访问地址: http://[${FIXED_IP%%/*}]:2469"
echo ""

# 1. 立即添加固定地址
echo "📡 正在添加固定 IPv6 地址..."
sudo ip -6 addr add $FIXED_IP dev $INTERFACE 2>/dev/null && echo "✅ 地址已添加" || echo "⚠️  地址可能已存在"

# 2. 验证
echo ""
echo "🔍 验证..."
ip -6 addr show dev $INTERFACE | grep $FIXED_SUFFIX

echo ""
echo "=============================="
echo "✅ 固定 IP 已配置！"
echo "📱 手机访问: http://[${FIXED_IP%%/*}]:2469"
echo ""

# 3. 询问是否要配置开机自动恢复
read -p "❓ 要配置开机自动设置此地址吗？(y/n): " AUTO
if [ "$AUTO" = "y" ] || [ "$AUTO" = "Y" ]; then
    SCRIPT_PATH=$(readlink -f "$0")
    
    # 创建 systemd 服务
    sudo tee /etc/systemd/system/pyclaw-ipv6.service > /dev/null <<EOF
[Unit]
Description=PyClaw Fixed IPv6 Address
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$SCRIPT_PATH --no-prompt
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable pyclaw-ipv6.service
    echo "✅ 已启用开机自启服务"
fi

# 如果是 --no-prompt 模式，不询问直接执行
if [ "$1" = "--no-prompt" ]; then
    exit 0
fi
