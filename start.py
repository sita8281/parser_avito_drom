import time
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import pickle
import zlib
from datetime import datetime
from tbot import TBot
from parse import AvitoParser, DromParser


def center_window(p, width, height):
    screen_width = p.winfo_screenwidth()
    screen_height = p.winfo_screenheight()
    win_width = width
    win_height = height
    x_coordinate = int((screen_width / 2) - (win_width / 2))
    y_coordinate = int((screen_height / 2) - (win_height / 2))
    return f'{win_width}x{win_height}+{x_coordinate}+{y_coordinate}'


class EntryWithMenu(ttk.Entry):
    """
    Обычный Entry виджет наследованный от ttk.Entry
    Добавлено простое меню: копировать, ставить и вырезать
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<Button-3>', self.open_menu)
        self.menu = tk.Menu(tearoff=0)
        self.menu.add_command(label='Копировать', command=self.copy)
        self.menu.add_command(label='Вставить', command=self.paste)
        self.menu.add_command(label='Вырезать', command=self.cut)

    def open_menu(self, e):
        self.menu.post(e.x_root, e.y_root)

    def copy(self):
        try:
            if self.selection_present():
                f_sel = self.index('sel.first')
                l_sel = self.index('sel.last')
                self.clipboard_clear()
                get = self.get()
                self.clipboard_append(get[f_sel:l_sel])
                return f_sel, l_sel
        except (tk.TclError, Exception):
            pass

    def paste(self):
        try:
            pst = self.clipboard_get()
            if pst:
                if self.selection_present():
                    f_sel = self.index('sel.first')
                    l_sel = self.index('sel.last')
                    self.delete(f_sel, l_sel)
                    self.insert(f_sel, pst)
                else:
                    indx = self.index('insert')
                    self.insert(indx, pst)
        except tk.TclError:
            pass

    def cut(self):
        sel = self.copy()
        if sel:
            self.delete(sel[0], sel[1])


class TitleFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.url_label = ttk.Label(self, text='URL:')
        self.url_entry = EntryWithMenu(self, width=70)
        self.token_label = ttk.Label(self, text='TOKEN:')
        self.token_entry = EntryWithMenu(self, width=70)

        self.url_label.grid(row=0, column=0)
        self.url_entry.grid(row=0, column=1, sticky='we', pady=5)
        self.token_label.grid(row=1, column=0)
        self.token_entry.grid(row=1, column=1, sticky='we', pady=5)

        self.columnconfigure(1, weight=1)

    def clear_all(self):
        self.url_entry.delete(0, 'end')
        self.token_entry.delete(0, 'end')

    def insert_data(self, data):
        self.clear_all()
        self.url_entry.insert('end', data['url'])
        self.token_entry.insert('end', data['token'])


class ProxyFrame(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text='Прокси')

        self.bool_proxy = tk.IntVar()
        self.bool_auth = tk.IntVar()
        self.bool_proxy.set(0)
        self.bool_auth.set(0)

        self.use_proxy_checkbox = ttk.Checkbutton(self, text='Использовать прокси', variable=self.bool_proxy)
        self.use_proxy_checkbox.bind('<Button-1>', self.state_proxy_all)
        self.auth_proxy_checkbox = ttk.Checkbutton(self, text='Прокси с авторизацией', variable=self.bool_auth)
        self.auth_proxy_checkbox.bind('<Button-1>', self.state_auth)

        self.proxy_label = ttk.Label(self, text='Socks5 Proxy:')
        self.proxy_entry = EntryWithMenu(self)
        self.login_label = ttk.Label(self, text='Login:')
        self.login_entry = EntryWithMenu(self)
        self.passw_label = ttk.Label(self, text='Password:')
        self.passw_entry = EntryWithMenu(self)

        self.use_proxy_checkbox.grid(row=0, column=0, columnspan=2, sticky='w')
        self.proxy_label.grid(row=1, column=0)
        self.proxy_entry.grid(row=1, column=1, pady=2, padx=5, sticky='we')
        self.auth_proxy_checkbox.grid(row=2, column=0, columnspan=2, sticky='w')
        self.login_label.grid(row=3, column=0)
        self.login_entry.grid(row=3, column=1, pady=0, padx=5, sticky='we')
        self.passw_label.grid(row=4, column=0)
        self.passw_entry.grid(row=4, column=1, pady=10, padx=5, sticky='we')

        self.columnconfigure(1, weight=1)

        self._disable_all()

    def state_proxy_all(self, ev=None):
        if self.bool_proxy.get():
            self.bool_auth.set(0)
            self._disable_all()
        else:
            self._enable_all()

    def state_auth(self, ev=None):
        if self.bool_auth.get():
            self.login_entry['state'] = 'disable'
            self.passw_entry['state'] = 'disable'
        else:
            self.login_entry['state'] = 'normal'
            self.passw_entry['state'] = 'normal'

    def _disable_all(self):
        self.proxy_entry['state'] = 'disable'
        self.auth_proxy_checkbox['state'] = 'disable'
        self.login_entry['state'] = 'disable'
        self.passw_entry['state'] = 'disable'
        self.auth_proxy_checkbox.unbind('<Button-1>')

    def _enable_all(self):
        self.proxy_entry['state'] = 'normal'
        self.auth_proxy_checkbox['state'] = 'normal'
        self.auth_proxy_checkbox.bind('<Button-1>', self.state_auth)

    def fill_entryes(self, data):
        proxy = data['proxy']
        self._enable_all()
        self.login_entry['state'] = 'normal'
        self.passw_entry['state'] = 'normal'
        self.clear_entryes()
        self.bool_proxy.set(1)
        self.bool_auth.set(1)

        self.proxy_entry.insert(tk.END, proxy['socks_proxy'])
        self.login_entry.insert(tk.END, proxy['login'])
        self.passw_entry.insert(tk.END, proxy['passw'])

        if not proxy['auth']:
            self.login_entry['state'] = 'disable'
            self.passw_entry['state'] = 'disable'
            self.bool_auth.set(0)

        if not proxy['use']:
            self._disable_all()
            self.bool_proxy.set(0)

    def clear_entryes(self):
        self.proxy_entry.delete(0, tk.END)
        self.login_entry.delete(0, tk.END)
        self.passw_entry.delete(0, tk.END)


class ParamsFrame(ttk.LabelFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(text='Параметры', *args, **kwargs)

        self.site = tk.StringVar()
        self.user_agent = tk.IntVar()
        self.site.set('avito')
        self.user_agent.set(0)

        self.avito_radiobutton = ttk.Radiobutton(self, text='Avito', variable=self.site, value='avito')
        self.drom_radiobutton = ttk.Radiobutton(self, text='Drom', variable=self.site, value='drom')

        self.count_requests_label = ttk.Label(self, text='Кол-во запросов:')
        self.count_requests_combobox = ttk.Combobox(
            self,
            width=4,
            state='readonly',
            values=[str(i) for i in range(1, 51)]
        )
        self.count_requests_combobox.set('20')
        self.count_requests_label2 = ttk.Label(self, text='за 1 минуту.')

        self.user_agent_checkbox = ttk.Checkbutton(self, text='Подмена User-Agent', variable=self.user_agent)

        self.avito_radiobutton.grid(row=0, column=0)
        self.drom_radiobutton.grid(row=0, column=1, pady=8)
        self.count_requests_label.grid(row=1, column=0, columnspan=5)
        self.count_requests_combobox.grid(row=2, column=0)
        self.count_requests_label2.grid(row=2, column=1)
        self.user_agent_checkbox.grid(row=3, column=0, columnspan=2, pady=15)

    def insert_data(self, data):
        params = data['params']
        self.site.set(params['site'])
        self.count_requests_combobox.set(params['count_requests'])
        self.user_agent.set(params['fake-ua'])


class BtnFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.load_button = ttk.Button(self, text='Load config')
        self.save_button = ttk.Button(self, text='Save config')
        self.start_button = ttk.Button(self, text='Start')
        self.stop_button = ttk.Button(self, text='Stop')

        self.load_button.grid(row=0, column=0, padx=10, sticky='we')
        self.save_button.grid(row=0, column=1, padx=10, sticky='we')
        self.start_button.grid(row=0, column=2, padx=10, sticky='we')
        self.stop_button.grid(row=0, column=3, padx=10, sticky='we')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

    def state_btns(self, state: str, btn=None):
        self.load_button['state'] = state
        self.save_button['state'] = state
        if btn == 'start':
            self.start_button['state'] = state
            self.stop_button['state'] = 'normal'
        elif btn == 'stop':
            self.start_button['state'] = state
            self.stop_button['state'] = 'disable'
        else:
            self.stop_button['state'] = state


class LogFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = 0

        self.img_warning = tk.PhotoImage(file='icons/warning.png')
        self.img_error = tk.PhotoImage(file='icons/error.png')
        self.img_good = tk.PhotoImage(file='icons/good.png')
        self.img_notify = tk.PhotoImage(file='icons/notify.png')

        s = ttk.Style()
        s.configure('f.Treeview', rowheight=17)

        self.tree = ttk.Treeview(
            self,
            height=15,
            selectmode='browse',
            style='f.Treeview',
            takefocus=False,
            show='tree'
        )

        self.scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scroll.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        self.scroll.grid(row=0, column=1, sticky='ns')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def insert_log(self, status, msg):
        if status == 'error':
            img = self.img_error
        elif status == 'notify':
            img = self.img_notify
        elif status == 'warning':
            img = self.img_warning
        elif status == 'good':
            img = self.img_good
        else:
            return
        date = datetime.fromtimestamp(int(time.time())).strftime('%H:%M:%S  %Y/%m/%d')
        a = self.tree.insert('', text=f'  {date}     {msg}', index='end', image=img)
        self.tree.see(a)
        if len(self.tree.get_children()) > 3000:
            lst = self.tree.get_children()[:200]
            for i in lst:
                self.tree.delete(i)

    def insert_pass(self):
        self.tree.insert('', text='', index='end')


class WaitBotWin(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.couter_anim = 0
        self.call_ = 1

        self.geometry(center_window(self, 300, 120))
        self.resizable(False, False)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.close_win)

        self.l_frame = tk.Frame(self)
        self.label_title = tk.Label(self.l_frame, text='Ожидание', fg='blue', font=('Segoe UI', 16, 'bold'), anchor='w')
        self.label_text = tk.Label(self, text='Отправьте команду "\\start" в телеграм-бот', font=('Segoe UI', 10))
        self.label_title.grid(row=0, column=0, sticky='w')
        self.l_frame.place(x=80, y=10)
        self.label_text.place(x=15, y=60)

        self.columnconfigure(0, weight=1)

        self.waiting_animation()

    def waiting_animation(self):
        if not self.call_:
            return
        self.label_title['text'] = 'Ожидание' + '.' * self.couter_anim
        self.couter_anim += 1
        if self.couter_anim > 5:
            self.couter_anim = 0
        self.after(300, self.waiting_animation)

    def destroy_win(self):
        app.success_wait = True
        self.call_ = 0
        self.destroy()

    def close_win(self):
        app.interupt_pars()
        self.call_ = 0
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry(center_window(self, 750, 600))
        self.data = None
        self.bot = None
        self._bot = None
        self.chat_id = None
        self.stop_flag_bot = False
        self.bot_th = None
        self.selenium_th = None
        self.success_wait = False
        self.selenium = None

        self.title_label = tk.Label(
            self,
            font=('Arial', 24, 'bold'),
            fg='white', bg='black',
            text='Avito & Drom parser'
        )
        self.url_and_token = TitleFrame(self)
        self.proxy_panel = ProxyFrame(self)
        self.requests_panel = ParamsFrame(self)
        self.buttons_panel = BtnFrame(self)
        self.log_view = LogFrame(self)

        self.title_label.grid(row=0, column=0, columnspan=2, sticky='we', pady=10, padx=10)
        self.url_and_token.grid(row=1, column=0, columnspan=2, sticky='we', padx=10)
        self.proxy_panel.grid(row=2, column=0, sticky='we', padx=10)
        self.requests_panel.grid(row=2, column=1, padx=10)
        self.buttons_panel.grid(row=3, column=0, columnspan=2, sticky='we', pady=20)
        self.log_view.grid(row=4, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)

        self.buttons_panel.save_button['command'] = self.save_data
        self.buttons_panel.load_button['command'] = self.load_data
        self.buttons_panel.start_button['command'] = self.start_pars
        self.buttons_panel.stop_button['command'] = self.stop_pars

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        self.log_view.insert_log('notify', '<Mihan & Kosta parser> запущен.')

    def get_dataset(self):
        """получить данные в виде словарной структуры"""
        url = self.url_and_token.url_entry.get()
        token = self.url_and_token.token_entry.get()
        use_proxy = self.proxy_panel.bool_proxy.get()
        proxy = self.proxy_panel.proxy_entry.get()
        auth_proxy = self.proxy_panel.bool_auth.get()
        login_proxy = self.proxy_panel.login_entry.get()
        passw_proxy = self.proxy_panel.passw_entry.get()
        site = self.requests_panel.site.get()
        count_req = self.requests_panel.count_requests_combobox.get()
        user_agent = self.requests_panel.user_agent.get()

        data = {
            'url': url,
            'token': token,
            'proxy': {
                'use': use_proxy,
                'socks_proxy': proxy,
                'auth': auth_proxy,
                'login': login_proxy,
                'passw': passw_proxy
            },
            'params': {
                'site': site,
                'count_requests': int(count_req),
                'fake-ua': user_agent
            }
        }

        return data

    def validate_dataset(self):
        """простая валидация полей программы"""
        data = self.get_dataset()

        for key, val in data.items():
            if val == '':
                return

        proxy = data['proxy']

        if proxy['use']:
            if not proxy['socks_proxy']:
                return

        if proxy['auth']:
            if not proxy['login']:
                return
            if not proxy['passw']:
                return
        return True

    def save_data(self, ev=None):
        """сохранить данные полей в файл"""
        if not self.validate_dataset():
            messagebox.showwarning('Предупреждение', 'Одно из полей не заполнено')
            self.log_view.insert_log('warning', 'Одно или несколько полей не заполнены.')
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.bin',
            initialfile='config',
            filetypes=(('BIN файлы', '*.bin'),),
        )
        if not path:
            return
        data = zlib.compress(pickle.dumps(self.get_dataset()))
        with open(file=path, mode='wb') as file:
            file.write(data)
        messagebox.showinfo('Информация', 'Файл сохранён успешно')
        self.log_view.insert_log('good', f'Конфигурация успешно сохарнена в файл: "{path}"')

    def load_data(self, ev=None):
        """загрузить данный полей из файла"""
        path = filedialog.askopenfilename(
            defaultextension='.bin',
            initialfile='config',
            filetypes=(('BIN файлы', '*.bin'),),
        )
        if not path:
            self.log_view.insert_log('error', 'Процесс загрузки файла прерван')
            return
        try:
            with open(file=path, mode='rb') as file:
                f = file.read()
            data = pickle.loads(zlib.decompress(f))

            self.proxy_panel.fill_entryes(data)
            self.url_and_token.insert_data(data)
            self.requests_panel.insert_data(data)

            self.log_view.insert_log('good', f'Конфигурация успешно загружена из файла: "{path}"')
        except Exception:
            self.log_view.insert_log('error', f'Не удалось загрузить файл конфигурации')
            return

    def start_pars(self, ev=None):

        self.log_view.insert_pass()

        if not self.validate_dataset():
            messagebox.showwarning('Предупреждение', 'Одно из полей не заполнено. '
                                                     'Для продолжения необходимо их заполнить')
            self.log_view.insert_log('warning', 'Одно или несколько полей не заполнены.')
            return

        self.success_wait = False
        self.log_view.insert_log('notify', 'Ожидание отправки команды в чат телеграм-бота...')
        wait_win = WaitBotWin()
        self.data = self.get_dataset()
        self._bot = TBot(self.data['token'], wait_win.destroy_win)
        self.bot = self._bot.get_bot()
        self.bot_th = threading.Thread(target=self.run_bot_thread, daemon=True)  # отдельный поток для bot.polling
        self.bot_th.start()
        self.buttons_panel.state_btns('disable', 'start')
        self.wait_window(wait_win)  # ожидание момента когда сообщение отправленное боту, сломает окно callback'ом

        if self.success_wait:
            self.log_view.insert_log('good', 'Соединение с ботом установлено успешно')
            proxy = None
            if self.data['proxy']['use']:
                proxy = self.data['proxy']['socks_proxy']
            if self.data['params']['site'] == 'avito':
                self.selenium = AvitoParser(
                    url=self.data['url'],
                    send_msg=self._bot.send_msg,
                    log=self.log_threadsafe,
                    timeout=60/self.data['params']['count_requests'],
                    proxy=proxy,
                    useragent=self.data['params']['fake-ua']
                )
            elif self.data['params']['site'] == 'drom':
                self.selenium = DromParser(
                    url=self.data['url'],
                    send_msg=self._bot.send_msg,
                    log=self.log_threadsafe,
                    timeout=60 / self.data['params']['count_requests'],
                    proxy=proxy,
                    useragent=self.data['params']['fake-ua']
                )
            else:
                self.success_wait = False
                self.log_view.insert_log('error', 'Не удаётся запустить парсинг, нужно указать сайт для парсинга')
                self.interupt_pars()
                return

            self.selenium_th = threading.Thread(target=self.selenium.run_pars, daemon=True)
            self.selenium_th.start()

    def stop_pars(self, ev=None):
        self.interupt_pars()

    def interupt_pars(self):
        """вызвается из окна ожидания"""
        self.log_view.insert_log('error', 'Процесс парсинга прерван.')
        self.log_view.insert_log('warning', 'Ожидание завершения вспомогательных потоков, не закрывайте программу.')
        self.stop_flag_bot = True
        self.bot.stop_bot()
        self.checking_threads()
        if self.success_wait:
            self.selenium.stop_selenium()
        self.buttons_panel.state_btns(state='disable')

    def checking_threads(self):
        if self.bot_th.is_alive():
            self.after(300, self.checking_threads)
            print('бот жив')
        elif self.success_wait:
            if not self.selenium_th.is_alive():
                self.success_wait = False
            self.after(300, self.checking_threads)
            print('селен')
        else:
            print('потоки остановлены')
            self.buttons_panel.state_btns('normal', 'stop')
            self.log_view.insert_log('notify', 'Программа доступна для парсинга')

    def log_threadsafe(self, log_type, msg):
        self.after_idle(lambda: self.log_view.insert_log(log_type, msg))

    def run_bot_thread(self):
        while True:
            try:
                self.bot.polling()
            except Exception:
                pass
            if self.stop_flag_bot:
                self.stop_flag_bot = False
                break
            time.sleep(1)


if __name__ == '__main__':
    app = App()
    app.mainloop()
