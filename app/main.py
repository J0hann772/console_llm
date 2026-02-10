import socket
import threading
import time
import os


from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


sessions = {}
SESSION_TTL = 7200  # 2 часа в секундах


def get_ai_response(user_id, text):
    now = time.time()

    if user_id not in sessions or (now - sessions[user_id]['last_time']) > SESSION_TTL:
        sessions[user_id] = {
            'history': [{"role": "system", "content": "Ты краткий ассистент для Linux-консоли."}],
            'last_time': now
        }

    sessions[user_id]['history'].append({"role": "user", "content": text})
    sessions[user_id]['last_time'] = now

    comp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=sessions[user_id]['history']
    )

    answer = comp.choices[0].message.content
    sessions[user_id]['history'].append({"role": "assistant", "content": answer})
    return answer


def handle_client(conn, addr):

    u_id = f"{addr[0]}:{addr[1]}"
    conn.send(b"Connected to AI Server. Type message and press Enter.\n> ")

    while True:
        try:

            data = conn.recv(4096).decode('utf-8').strip()
            if not data or data.lower() in ['exit', 'quit']:
                break


            response = get_ai_response(u_id, data)


            conn.send(f"\n{response}\n\n> ".encode('utf-8'))
        except Exception as e:
            print(f"ОШИБКА: {e}")
            break

    conn.close()


def start():
    # Создаем TCP сокет
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 5000))
    s.listen(10)
    print("Сервер готов. Команда для Linux: nc <ip> 5000")

    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()


if __name__ == "__main__":
    start()