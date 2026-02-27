import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from web3 import Web3
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# ====== 网络配置 (仅 EVM) ======
NETWORKS = {
    "Polygon": {
        "rpc": "https://polygon-rpc.com",
        "explorer": "https://polygonscan.com/address/"
    },
    "Polygon Testnet (Mumbai)": {
        "rpc": "https://rpc-mumbai.maticvigil.com",
        "explorer": "https://mumbai.polygonscan.com/address/"
    },
    "BSC": {
        "rpc": "https://bsc-dataseed.binance.org",
        "explorer": "https://bscscan.com/address/"
    },
    "BSC Testnet": {
        "rpc": "https://data-seed-prebsc-1-s1.binance.org:8545",
        "explorer": "https://testnet.bscscan.com/address/"
    }
}

# ====== 全局变量 ======
current_network = "Polygon"
w3 = None
RETRY_CONFIG = {
    'max_attempts': 3,      # 最大重试次数
    'base_delay': 1,        # 首次重试延迟(秒)
    'max_delay': 10,        # 最大延迟(秒)
    'timeout': 15           # 连接超时时间(秒)
}

# ====== 客户端初始化 (带自动重连) ======
def init_client(network_name, is_retry=False, attempt=1):
    """初始化对应网络的 Web3 客户端，支持自动重连"""
    global w3, current_network
    
    network = NETWORKS.get(network_name)
    if not network:
        raise ValueError(f"未知网络: {network_name}")
    
    current_network = network_name
    rpc_url = network["rpc"]
    
    # 更新UI状态
    def update_status(message, color="black"):
        if status_label:
            root.after(0, lambda: status_label.config(text=message, fg=color))
        if text_result and not is_retry and attempt == 1:
            root.after(0, lambda: text_result.insert(tk.END, f"{message}\n"))
    
    try:
        status_msg = f"{'🔄 重试连接中' if is_retry else '🔗 连接中'} ({attempt}/{RETRY_CONFIG['max_attempts']})..."
        update_status(status_msg, "orange")
        
        # 创建带超时的Provider
        provider = Web3.HTTPProvider(
            rpc_url, 
            request_kwargs={'timeout': RETRY_CONFIG['timeout']}
        )
        new_w3 = Web3(provider)
        
        # 测试连接（获取当前区块号）
        block_number = new_w3.eth.block_number
        if new_w3.is_connected():
            w3 = new_w3
            success_msg = f"✅ 已连接到 {network_name} (区块: {block_number})"
            update_status(success_msg, "green")
            if text_result and not is_retry:
                root.after(0, lambda: text_result.insert(tk.END, f"{success_msg}\n"))
            
            # 启用重连按钮（如果是重连成功的）
            if reconnect_btn:
                root.after(0, lambda: reconnect_btn.config(state="normal", text="🔄 重连"))
            
            return True
        else:
            raise ConnectionError("Web3.is_connected() 返回 False")
            
    except Exception as e:
        error_msg = f"连接尝试 {attempt} 失败: {str(e)[:60]}"
        update_status(error_msg, "red")
        
        # 计算是否继续重试
        if attempt < RETRY_CONFIG['max_attempts']:
            # 指数退避计算延迟时间
            delay = min(RETRY_CONFIG['max_delay'], 
                       RETRY_CONFIG['base_delay'] * (2 ** (attempt - 1)))
            
            # 更新状态显示等待信息
            wait_msg = f"⏳ {delay}秒后第{attempt+1}次重试..."
            update_status(wait_msg, "orange")
            
            # 安排下一次重试
            root.after(int(delay * 1000), 
                      lambda: init_client(network_name, True, attempt + 1))
            return False
        else:
            # 所有重试都失败
            final_error = f"❌ 无法连接到 {network_name}，已重试{attempt}次"
            update_status(final_error, "red")
            if text_result:
                root.after(0, lambda: text_result.insert(
                    tk.END, f"{final_error}\n建议：1.检查网络 2.稍后重试 3.切换其他网络\n"))
            
            # 启用重连按钮
            if reconnect_btn:
                root.after(0, lambda: reconnect_btn.config(state="normal", text="🔄 重连"))
            
            raise ConnectionError(final_error)

# ====== 手动重连函数 ======
def manual_reconnect():
    """手动触发重连"""
    if not current_network:
        messagebox.showinfo("提示", "请先选择一个网络")
        return
    
    # 禁用按钮避免重复点击
    if reconnect_btn:
        reconnect_btn.config(state="disabled", text="连接中...")
    
    # 在新线程中执行重连
    threading.Thread(target=perform_reconnect, daemon=True).start()

def perform_reconnect():
    """执行重连操作"""
    try:
        success = init_client(current_network, is_retry=False, attempt=1)
        if success:
            root.after(0, lambda: text_result.insert(
                tk.END, f"[手动重连] {current_network} 连接恢复成功\n"))
    except:
        pass  # 错误信息已在init_client中显示

# ====== 连接检查装饰器 ======
def check_connection(func):
    """检查Web3连接状态的装饰器"""
    def wrapper(*args, **kwargs):
        if not w3 or not w3.is_connected():
            # 尝试自动重连一次
            try:
                status_label.config(text="🔁 连接中断，尝试重连...", fg="orange")
                if init_client(current_network, is_retry=True, attempt=1):
                    status_label.config(text=f"✅ 已重新连接到: {current_network}", fg="green")
                else:
                    messagebox.showwarning("连接中断", "网络连接已断开，请检查网络或重试")
                    return None
            except:
                messagebox.showerror("连接错误", "无法连接到网络，请检查RPC配置")
                return None
        return func(*args, **kwargs)
    return wrapper

# ====== 代理合约检测函数 ======
@check_connection
def get_storage_at(contract_addr, slot):
    """统一的存储读取函数"""
    return w3.eth.get_storage_at(w3.to_checksum_address(contract_addr), slot)

def get_implementation_eip1967(proxy_addr):
    """EIP-1967 标准实现检测"""
    slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
    impl_bytes32 = get_storage_at(proxy_addr, int(slot, 16))
    
    if impl_bytes32 == b'\x00' * 32:
        return None
    
    impl_hex = '0x' + impl_bytes32[-20:].hex()
    return w3.to_checksum_address(impl_hex)

def get_implementation_beacon_proxy(proxy_addr):
    """Beacon 代理实现检测"""
    beacon_slot = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
    beacon_bytes32 = get_storage_at(proxy_addr, int(beacon_slot, 16))
    
    if beacon_bytes32 == b'\x00' * 32:
        return None
    
    beacon_hex = '0x' + beacon_bytes32[-20:].hex()
    beacon_addr = w3.to_checksum_address(beacon_hex)
    
    # Beacon 合约 ABI（仅 implementation 函数）
    beacon_abi = '[{"inputs":[],"name":"implementation","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]'
    
    try:
        beacon_contract = w3.eth.contract(address=beacon_addr, abi=beacon_abi)
        impl = beacon_contract.functions.implementation().call()
        return w3.to_checksum_address(impl)
    except Exception as e:
        print(f"Beacon 查询失败: {e}")
        return None

def get_implementation_fallback(proxy_addr):
    """回退方法检测（旧版/自定义代理）"""
    for slot in [0, 1, 51]:
        data = get_storage_at(proxy_addr, slot)
        if data != b'\x00' * 32:
            addr_hex = '0x' + data[-20:].hex()
            addr = w3.to_checksum_address(addr_hex)
            # 检查是否有代码（是合约地址）
            if w3.eth.get_code(addr) != b'':
                return addr
    return None

@check_connection
def get_proxy_implementation(proxy_addr):
    """主检测函数"""
    try:
        # 标准化地址格式
        proxy_addr = w3.to_checksum_address(proxy_addr.strip())
        
        # 1. 尝试 EIP-1967
        impl = get_implementation_eip1967(proxy_addr)
        if impl:
            return f"✅ EIP-1967 Implementation: {impl}", impl
        
        # 2. 尝试 Beacon Proxy
        impl = get_implementation_beacon_proxy(proxy_addr)
        if impl:
            return f"✅ Beacon Proxy Implementation: {impl}", impl
        
        # 3. 尝试回退方法
        impl = get_implementation_fallback(proxy_addr)
        if impl:
            return f"⚠️  旧版/自定义 Implementation: {impl}", impl
        
        return f"❌ {proxy_addr} 未检测到实现合约", None
        
    except ValueError as e:
        if "checksum" in str(e).lower():
            return f"❌ {proxy_addr} 地址格式错误（请检查校验和）", None
        return f"❌ {proxy_addr} 地址错误: {str(e)[:50]}", None
    except Exception as e:
        return f"❌ {proxy_addr} 查询失败: {str(e)[:80]}", None

# ====== GUI 函数 ======
def on_network_change(event):
    """网络切换事件处理"""
    network = network_var.get()
    # 在新线程中切换网络，避免界面卡顿
    threading.Thread(target=switch_network_thread, args=(network,), daemon=True).start()

def switch_network_thread(network):
    """切换网络的线程函数"""
    try:
        if init_client(network):
            root.after(0, lambda: status_label.config(
                text=f"✅ 已连接到: {network}", fg="green"))
            root.after(0, lambda: text_result.insert(
                tk.END, f"[{network}] 网络连接成功\n"))
            root.after(0, lambda: text_result.see(tk.END))
    except Exception as e:
        root.after(0, lambda: status_label.config(
            text=f"❌ 连接错误: {str(e)[:30]}", fg="red"))

def query_single():
    """单地址查询"""
    addr = entry_address.get().strip()
    if not addr:
        messagebox.showwarning("警告", "请输入合约地址！")
        return
    
    if not w3 or not w3.is_connected():
        messagebox.showwarning("警告", "网络未连接，请先连接网络！")
        return
    
    # 显示查询状态
    text_result.insert(tk.END, f"🔍 查询中: {addr}\n")
    text_result.see(tk.END)
    
    # 在新线程中查询
    threading.Thread(target=query_and_display, args=(addr,), daemon=True).start()

def query_and_display(addr):
    """后台查询并显示结果"""
    result_text, impl_addr = get_proxy_implementation(addr)
    network_info = NETWORKS.get(current_network, {})
    
    # 在 GUI 线程中更新结果
    def update_display():
        text_result.insert(tk.END, f"📍 地址: {addr}\n")
        text_result.insert(tk.END, f"📝 结果: {result_text}\n")
        
        # 如果有实现地址，添加浏览器链接
        if impl_addr and "未检测" not in result_text and "失败" not in result_text:
            explorer = network_info.get("explorer", "")
            if explorer:
                link = f"{explorer}{impl_addr}"
                text_result.insert(tk.END, f"   🔗 浏览器: {link}\n")
        
        text_result.insert(tk.END, "-" * 70 + "\n")
        text_result.see(tk.END)
    
    root.after(0, update_display)

def query_file():
    """批量文件查询"""
    if not w3 or not w3.is_connected():
        messagebox.showwarning("警告", "网络未连接，请先连接网络！")
        return
    
    file_path = filedialog.askopenfilename(
        title="选择地址文件",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not file_path:
        return
    
    try:
        with open(file_path, "r") as f:
            addresses = [line.strip() for line in f.readlines() if line.strip()]
        
        if not addresses:
            messagebox.showwarning("警告", "文件为空或格式不正确！")
            return
        
        text_result.insert(tk.END, f"📁 批量查询开始，共 {len(addresses)} 个地址\n")
        text_result.see(tk.END)
        
        # 使用线程池批量查询（限制并发数，避免请求过多）
        def batch_query():
            with ThreadPoolExecutor(max_workers=5) as executor:
                for addr in addresses:
                    executor.submit(query_and_display, addr)
                    time.sleep(0.1)  # 轻微延迟，避免请求过快
        
        threading.Thread(target=batch_query, daemon=True).start()
        
    except Exception as e:
        messagebox.showerror("错误", f"读取文件失败: {e}")

def clear_results():
    """清空结果"""
    text_result.delete(1.0, tk.END)

def copy_selected():
    """复制选中的文本"""
    try:
        selected = text_result.get(tk.SEL_FIRST, tk.SEL_LAST)
        if selected:
            root.clipboard_clear()
            root.clipboard_append(selected)
            status_label.config(text="📋 已复制到剪贴板", fg="blue")
    except:
        pass

def export_results():
    """导出结果到文件"""
    if not text_result.get(1.0, tk.END).strip():
        messagebox.showwarning("警告", "没有内容可以导出！")
        return
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text_result.get(1.0, tk.END))
            status_label.config(text=f"💾 已导出到: {file_path}", fg="green")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")

# ====== Tkinter GUI ======
root = tk.Tk()
root.title("EVM 代理合约查询工具 (Polygon & BSC) - 增强连接版")
root.geometry("900x650")

# 设置样式
style = ttk.Style()
style.theme_use('clam')

# 顶部框架 - 网络选择
frame_top = tk.Frame(root, bg="#f0f0f0", pady=8)
frame_top.pack(fill=tk.X, padx=10, pady=5)

tk.Label(frame_top, text="🌐 选择网络:", bg="#f0f0f0", font=("Arial", 10)).pack(side=tk.LEFT)
network_var = tk.StringVar(value="Polygon")
network_combo = ttk.Combobox(frame_top, textvariable=network_var, 
                            values=list(NETWORKS.keys()), width=22, state="readonly")
network_combo.pack(side=tk.LEFT, padx=5)
network_combo.bind("<<ComboboxSelected>>", on_network_change)

# 手动重连按钮
reconnect_btn = tk.Button(frame_top, text="🔄 重连", command=manual_reconnect,
                         bg="#FF9800", fg="white", font=("Arial", 9),
                         width=8, cursor="hand2")
reconnect_btn.pack(side=tk.LEFT, padx=10)

status_label = tk.Label(frame_top, text="正在初始化...", bg="#f0f0f0", fg="gray", font=("Arial", 9))
status_label.pack(side=tk.LEFT, padx=20)

# 输入框架
frame_input = tk.Frame(root)
frame_input.pack(pady=10, padx=10, fill=tk.X)

tk.Label(frame_input, text="📝 合约地址 (0x...):", font=("Arial", 10)).pack(side=tk.LEFT)
entry_address = tk.Entry(frame_input, width=70, font=("Consolas", 10))
entry_address.pack(side=tk.LEFT, padx=5)
entry_address.bind("<Return>", lambda event: query_single())  # 回车键查询

# 按钮框架
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=8)

btn_style = {"width": 12, "font": ("Arial", 9), "cursor": "hand2"}

btn_query = tk.Button(frame_buttons, text="🔍 查询", command=query_single, 
                      bg="#4CAF50", fg="white", **btn_style)
btn_query.pack(side=tk.LEFT, padx=4)

btn_file = tk.Button(frame_buttons, text="📁 批量查询", command=query_file,
                     bg="#2196F3", fg="white", **btn_style)
btn_file.pack(side=tk.LEFT, padx=4)

btn_clear = tk.Button(frame_buttons, text="🗑️  清空", command=clear_results,
                      bg="#757575", fg="white", **btn_style)
btn_clear.pack(side=tk.LEFT, padx=4)

btn_export = tk.Button(frame_buttons, text="💾 导出", command=export_results,
                       bg="#FF9800", fg="white", **btn_style)
btn_export.pack(side=tk.LEFT, padx=4)

# 结果文本框框架
frame_result = tk.LabelFrame(root, text="查询结果", font=("Arial", 10), padx=5, pady=5)
frame_result.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# 添加右键菜单
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="复制", command=copy_selected)
context_menu.add_separator()
context_menu.add_command(label="清空", command=clear_results)
context_menu.add_command(label="导出", command=export_results)

def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)

# 创建滚动文本框
text_result = scrolledtext.ScrolledText(frame_result, width=110, height=25,
                                       wrap=tk.WORD, font=("Consolas", 9),
                                       bg="#f9f9f9", relief=tk.FLAT)
text_result.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
text_result.bind("<Button-3>", show_context_menu)

# 底部状态栏
frame_bottom = tk.Frame(root, bg="#e8e8e8", height=25)
frame_bottom.pack(fill=tk.X, side=tk.BOTTOM)

tk.Label(frame_bottom, text="💡 支持: EIP-1967 • Beacon Proxy • 旧版代理 | 自动重连: 3次 (指数退避)", 
         bg="#e8e8e8", fg="#555", font=("Arial", 8)).pack(side=tk.LEFT, padx=10)

# 初始化默认网络
def initialize_network():
    """初始化网络连接"""
    try:
        init_client("Polygon")
    except Exception as e:
        # 错误信息已在init_client中显示
        pass

# 在新线程中初始化网络，避免界面卡顿
threading.Thread(target=initialize_network, daemon=True).start()

# 启动 GUI
root.mainloop()