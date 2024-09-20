import random
import tkinter as tk
from tkinter import messagebox
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, ImageTk

class VegasGame:
    def __init__(self, num_players):
        self.num_players = num_players
        self.players = [Player(i) for i in range(num_players)]
        self.casinos = [Casino(i) for i in range(1, 7)]
        self.current_round = 1
        self.start_player = 0
        self.current_player = 0
        self.setup_game()

    def setup_game(self):
        money_cards = [10000] * 6 + [20000] * 8 + [30000] * 8 + [40000] * 6 + \
                      [50000] * 6 + [60000] * 5 + [70000] * 5 + [80000] * 5 + [90000] * 5
        random.shuffle(money_cards)
        for casino in self.casinos:
            casino.add_money(money_cards)

    def play_round(self):
        player = self.players[self.current_player]
        if player.dice:
            player.roll_dice()
            return True
        return False

    def place_dice(self, casino_index):
        player = self.players[self.current_player]
        if casino_index in player.current_roll:
            count = player.current_roll.count(casino_index)
            player.dice -= count
            self.casinos[casino_index - 1].add_dice(player.id, count)
            player.current_roll = [d for d in player.current_roll if d != casino_index]
            self.next_player()
            return True
        return False

    def next_player(self):
        self.current_player = (self.current_player + 1) % self.num_players
        while self.players[self.current_player].dice == 0:
            self.current_player = (self.current_player + 1) % self.num_players
            if self.current_player == self.start_player:
                self.end_round()
                break

    def end_round(self):
        winnings = {player.id: [] for player in self.players}
        for casino in self.casinos:
            casino_winnings = casino.distribute_money(self.players)
            for player_id, amount in casino_winnings.items():
                winnings[player_id].append((casino.number, amount))
        
        for player in self.players:
            player.reset_dice()
        
        # 새로운 돈 카드 준비
        money_cards = [10000] * 6 + [20000] * 8 + [30000] * 8 + [40000] * 6 + \
                      [50000] * 6 + [60000] * 5 + [70000] * 5 + [80000] * 5 + [90000] * 5
        random.shuffle(money_cards)
        
        for casino in self.casinos:
            casino.reset(money_cards)
        
        self.current_round += 1
        self.start_player = (self.start_player + 1) % self.num_players
        self.current_player = self.start_player
        
        return winnings

    def get_winner(self):
        return max(self.players, key=lambda p: (p.money, p.card_count))

class Player:
    def __init__(self, id):
        self.id = id
        self.dice = 8
        self.money = 0
        self.card_count = 0
        self.current_roll = []

    def roll_dice(self):
        self.current_roll = [random.randint(1, 6) for _ in range(self.dice)]
        self.current_roll.sort()  # 주사위 결과를 정렬

    def get_dice_count(self):
        return Counter(self.current_roll)  # 각 숫자별 주사위 개수를 반환

    def reset_dice(self):
        self.dice = 8
        self.current_roll = []

    def add_money(self, amount):
        self.money += amount
        self.card_count += 1

class Casino:
    def __init__(self, number):
        self.number = number
        self.dice = {}
        self.money = []

    def add_dice(self, player_id, count):
        self.dice[player_id] = self.dice.get(player_id, 0) + count

    def add_money(self, money_cards):
        total = 0
        while total < 50000 and money_cards:
            card = money_cards.pop()
            self.money.append(card)
            total += card

    def distribute_money(self, players):
        dice_counts = sorted(self.dice.items(), key=lambda x: x[1], reverse=True)
        unique_counts = {}
        for player_id, count in dice_counts:
            if count not in unique_counts:
                unique_counts[count] = player_id
        
        winnings = {}
        for count, player_id in sorted(unique_counts.items(), reverse=True):
            if self.money:
                amount = self.money.pop(0)
                players[player_id].add_money(amount)
                winnings[player_id] = amount
            else:
                winnings[player_id] = 0
        
        return winnings

    def reset(self, money_cards=None):
        self.dice.clear()
        self.money.clear()  # 기존 돈을 모두 제거
        if money_cards:
            self.add_money(money_cards)  # 새로운 돈 추가

class VegasGameGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("라스베가스 게임")
        self.master.geometry("1200x800")
        self.game = None
        self.load_images()  # 이미지 로드를 먼저 수행
        self.setup_ui()

    def setup_ui(self):
        self.start_frame = tk.Frame(self.master)
        self.start_frame.pack(padx=20, pady=20)

        tk.Label(self.start_frame, text="플레이어 수:").pack(side=tk.LEFT)
        self.player_count = tk.StringVar(value="2")
        tk.OptionMenu(self.start_frame, self.player_count, "2", "3", "4", "5").pack(side=tk.LEFT)
        tk.Button(self.start_frame, text="게임 시작", command=self.start_game).pack(side=tk.LEFT)

        self.game_frame = tk.Frame(self.master)
        self.casino_frames = [tk.Frame(self.game_frame) for _ in range(6)]
        self.casino_money_labels = []
        self.casino_dice_labels = []
        for i, frame in enumerate(self.casino_frames):
            frame.grid(row=i//3, column=i%3, padx=20, pady=20)
            tk.Label(frame, image=self.casino_images[i]).pack()  # 카지노 이미지 사용
            money_label = tk.Label(frame, text="", compound=tk.LEFT, image=self.money_image)  # 돈 이미지 사용
            money_label.pack()
            self.casino_money_labels.append(money_label)
            dice_label = tk.Label(frame, text="")
            dice_label.pack()
            self.casino_dice_labels.append(dice_label)
            tk.Button(frame, text="주사위 배치", command=lambda x=i+1: self.place_dice(x)).pack()

        self.info_frame = tk.Frame(self.master)
        self.info_frame.pack(pady=10)
        self.info_label = tk.Label(self.info_frame, text="")
        self.info_label.pack()

        self.dice_frame = tk.Frame(self.master)
        self.dice_frame.pack(pady=10)
        self.dice_labels = [tk.Label(self.dice_frame) for _ in range(6)]
        for i, label in enumerate(self.dice_labels):
            label.pack(side=tk.LEFT, padx=5)
            label.config(image=self.dice_images[i], text=f"{i+1}", compound=tk.BOTTOM)

        self.roll_button = tk.Button(self.master, text="주사위 굴리기", command=self.roll_dice, state=tk.DISABLED)
        self.roll_button.pack(pady=10)

        self.player_money_frame = tk.Frame(self.master)
        self.player_money_frame.pack(pady=10)
        self.player_money_labels = []

    def start_game(self):
        num_players = int(self.player_count.get())
        self.game = VegasGame(num_players)
        self.start_frame.pack_forget()
        self.game_frame.pack()
        self.update_info()
        self.update_casino_money()
        self.update_player_money()
        self.roll_button.config(state=tk.NORMAL)

    def roll_dice(self):
        if self.game and self.game.play_round():
            self.update_info()
            self.update_player_money()
            self.roll_button.config(state=tk.DISABLED)
        else:
            self.end_game()

    def place_dice(self, casino_index):
        if self.game and self.game.place_dice(casino_index):
            self.update_info()
            self.update_casino_money()
            self.update_player_money()
            if self.game.current_round <= 4:
                if all(player.dice == 0 for player in self.game.players):
                    self.end_round()
                else:
                    self.roll_button.config(state=tk.NORMAL)
            else:
                self.end_game()

    def end_round(self):
        winnings = self.game.end_round()
        self.show_round_results(winnings)
        self.update_casino_money()
        self.update_player_money()
        if self.game.current_round <= 4:
            self.roll_button.config(state=tk.NORMAL)
        else:
            self.end_game()

    def show_round_results(self, winnings):
        result_text = f"라운드 {self.game.current_round - 1} 결과:\n\n"
        for player_id, player_winnings in winnings.items():
            player = self.game.players[player_id]
            result_text += f"플레이어 {player_id + 1}:\n"
            for casino_number, amount in player_winnings:
                if amount > 0:
                    result_text += f"  카지노 {casino_number}에서 ${amount} 획득\n"
            result_text += f"  총 잔액: ${player.money}\n\n"
        
        messagebox.showinfo("라운드 결과", result_text)

    def update_info(self):
        player = self.game.players[self.game.current_player]
        self.info_label.config(text=f"라운드: {self.game.current_round}, 플레이어: {player.id + 1}, 남은 주사위: {player.dice}")
        
        dice_count = player.get_dice_count()
        for i, label in enumerate(self.dice_labels):
            count = dice_count[i+1]
            label.config(image=self.dice_images[i], text=f"{i+1}: {count}", compound=tk.BOTTOM)

    def update_casino_money(self):
        for i, casino in enumerate(self.game.casinos):
            money_str = ", ".join([f"${m}" for m in casino.money])
            self.casino_money_labels[i].config(text=f" {money_str}", image=self.money_image, compound=tk.LEFT)
            
            dice_str = ", ".join([f"P{p+1}: {c}" for p, c in casino.dice.items()])
            self.casino_dice_labels[i].config(text=f"주사위: {dice_str}")

    def update_player_money(self):
        for label in self.player_money_labels:
            label.destroy()
        self.player_money_labels.clear()

        for player in self.game.players:
            label = tk.Label(self.player_money_frame, text=f"플레이어 {player.id + 1}: ${player.money}", image=self.money_image, compound=tk.LEFT)
            label.pack(side=tk.LEFT, padx=5)
            self.player_money_labels.append(label)
        
        self.player_money_frame.update()

    def end_game(self):
        winner = self.game.get_winner()
        messagebox.showinfo("게임 종료", f"승자: 플레이어 {winner.id + 1} (${winner.money}, 카드 {winner.card_count}장)")
        self.master.quit()

    def load_images(self):
        self.dice_images = [self.create_dice_image(i) for i in range(1, 7)]
        self.casino_images = [self.create_casino_image(i) for i in range(1, 7)]
        self.money_image = self.create_money_image()

    def create_dice_image(self, number):
        size = 50  # 주사위 크기를 더 크게 설정
        dot_size = 6
        image = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, size-1, size-1], outline='black')

        if number in [1, 3, 5]:
            draw.ellipse([(size//2 - dot_size//2, size//2 - dot_size//2),
                          (size//2 + dot_size//2, size//2 + dot_size//2)], fill='black')

        if number in [2, 3, 4, 5, 6]:
            draw.ellipse([(size//4 - dot_size//2, size//4 - dot_size//2),
                          (size//4 + dot_size//2, size//4 + dot_size//2)], fill='black')
            draw.ellipse([(3*size//4 - dot_size//2, 3*size//4 - dot_size//2),
                          (3*size//4 + dot_size//2, 3*size//4 + dot_size//2)], fill='black')

        if number in [4, 5, 6]:
            draw.ellipse([(3*size//4 - dot_size//2, size//4 - dot_size//2),
                          (3*size//4 + dot_size//2, size//4 + dot_size//2)], fill='black')
            draw.ellipse([(size//4 - dot_size//2, 3*size//4 - dot_size//2),
                          (size//4 + dot_size//2, 3*size//4 + dot_size//2)], fill='black')

        if number == 6:
            draw.ellipse([(size//4 - dot_size//2, size//2 - dot_size//2),
                          (size//4 + dot_size//2, size//2 + dot_size//2)], fill='black')
            draw.ellipse([(3*size//4 - dot_size//2, size//2 - dot_size//2),
                          (3*size//4 + dot_size//2, size//2 + dot_size//2)], fill='black')

        return ImageTk.PhotoImage(image)

    def create_casino_image(self, number):
        image = Image.new('RGB', (100, 100), color='lightblue')
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, 99, 99], outline='black')
        font = ImageFont.load_default()
        text = f"Casino {number}"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((100-w)/2, (100-h)/2), text, fill='black', font=font)
        return ImageTk.PhotoImage(image)

    def create_money_image(self):
        image = Image.new('RGB', (30, 20), color='lightgreen')
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, 29, 19], outline='black')
        font = ImageFont.load_default()
        text = "$"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((30-w)/2, (20-h)/2), text, fill='black', font=font)
        return ImageTk.PhotoImage(image)

if __name__ == "__main__":
    root = tk.Tk()
    app = VegasGameGUI(root)
    root.mainloop()
