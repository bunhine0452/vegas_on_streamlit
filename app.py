import streamlit as st
import random
from collections import Counter
from PIL import Image, ImageDraw
import io
import streamlit_option_menu   
st.set_page_config(layout="wide")
class VegasGame:
    def __init__(self, num_players):
        self.num_players = num_players
        self.players = [Player(i) for i in range(num_players)]
        self.casinos = [Casino(i) for i in range(1, 7)]
        self.current_round = 1
        self.start_player = 0
        self.current_player = 0
        self.dice_rolled = False
        self.setup_game()

    def setup_game(self):
        money_cards = [10000] * 6 + [20000] * 8 + [30000] * 8 + [40000] * 6 + \
                      [50000] * 6 + [60000] * 5 + [70000] * 5 + [80000] * 5 + [90000] * 5
        random.shuffle(money_cards)
        for casino in self.casinos:
            casino.add_money(money_cards)

    def play_round(self):
        player = self.players[self.current_player]
        if player.dice and not self.dice_rolled:
            player.roll_dice()
            self.dice_rolled = True
            return True
        return False

    def place_dice(self, casino_index):
        player = self.players[self.current_player]
        regular_count = player.current_roll.count(casino_index)
        dealer_count = player.current_dealer_roll.count(casino_index)
        
        if regular_count > 0 or dealer_count > 0:
            # 일반 주사위 배치
            for _ in range(regular_count):
                player.current_roll.remove(casino_index)
                player.dice -= 1
                self.casinos[casino_index - 1].add_dice(player.id, 1)
            
            # 딜러 주사위 배치
            for _ in range(dealer_count):
                player.current_dealer_roll.remove(casino_index)
                player.dealer_dice -= 1
                self.casinos[casino_index - 1].add_dealer_dice(1)
            
            self.next_player()  # 배팅 후 바로 다음 플레이어로 넘어감
            return True
        return False

    def next_player(self):
        self.current_player = (self.current_player + 1) % self.num_players
        while self.players[self.current_player].dice == 0 and self.players[self.current_player].dealer_dice == 0:
            self.current_player = (self.current_player + 1) % self.num_players
            if self.current_player == self.start_player:
                self.end_round()
                break
        self.dice_rolled = False

    def end_round(self):
        winnings = {player.id: [] for player in self.players}
        for casino in self.casinos:
            casino_winnings = casino.distribute_money(self.players)
            for player_id, amount in casino_winnings.items():
                winnings[player_id].append((casino.number, amount))
        
        for player in self.players:
            player.reset_dice()
            player.dealer_dice = 4
        
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
        self.dealer_dice = 4
        self.money = 0
        self.card_count = 0
        self.current_roll = []
        self.current_dealer_roll = []

    def roll_dice(self):
        self.current_roll = [random.randint(1, 6) for _ in range(self.dice)]
        self.current_roll.sort()
        self.current_dealer_roll = [random.randint(1, 6) for _ in range(self.dealer_dice)]
        self.current_dealer_roll.sort()

    def get_dice_count(self):
        return Counter(self.current_roll)

    def get_dealer_dice_count(self):
        return Counter(self.current_dealer_roll)

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
        self.dealer_dice = 0  # 딜러 주사위 개수 초기화
        self.money = []

    def add_dice(self, player_id, count):
        self.dice[player_id] = self.dice.get(player_id, 0) + count

    def add_dealer_dice(self, count):
        self.dealer_dice += count  # 딜러 주사위 개수 증가

    def add_money(self, money_cards):
        total = 0
        while total < 50000 and money_cards:
            card = money_cards.pop()
            self.money.append(card)
            total += card

    def distribute_money(self, players):
        dice_counts = sorted(self.dice.items(), key=lambda x: x[1], reverse=True)
        
        if self.dealer_dice >= max([count for _, count in dice_counts], default=0):
            return {}

        unique_counts = {}
        for player_id, count in dice_counts:
            if count > self.dealer_dice and count not in unique_counts:
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
        self.dealer_dice = 0  # 딜러 주사위 개수 초기화
        self.money.clear()
        if money_cards:
            self.add_money(money_cards)

def create_dice_image(number):
    size = 50
    dot_size = 6
    image = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, size-1, size-1], outline='black')

    dots = {
        1: [(25, 25)],
        2: [(17, 17), (33, 33)],
        3: [(17, 17), (25, 25), (33, 33)],
        4: [(17, 17), (17, 33), (33, 17), (33, 33)],
        5: [(17, 17), (17, 33), (25, 25), (33, 17), (33, 33)],
        6: [(17, 17), (17, 25), (17, 33), (33, 17), (33, 25), (33, 33)]
    }

    for dot in dots[number]:
        draw.ellipse([dot[0]-dot_size//2, dot[1]-dot_size//2,
                      dot[0]+dot_size//2, dot[1]+dot_size//2], fill='black')

    return image

def create_dealer_dice_image(number):
    size = 50
    dot_size = 6
    image = Image.new('RGB', (size, size), color='lightgray')
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, size-1, size-1], outline='black')

    dots = {
        1: [(25, 25)],
        2: [(17, 17), (33, 33)],
        3: [(17, 17), (25, 25), (33, 33)],
        4: [(17, 17), (17, 33), (33, 17), (33, 33)],
        5: [(17, 17), (17, 33), (25, 25), (33, 17), (33, 33)],
        6: [(17, 17), (17, 25), (17, 33), (33, 17), (33, 25), (33, 33)]
    }

    for dot in dots[number]:
        draw.ellipse([dot[0]-dot_size//2, dot[1]-dot_size//2,
                      dot[0]+dot_size//2, dot[1]+dot_size//2], fill='red')

    return image

def create_casino_image(number):
    image = Image.new('RGB', (100, 100), color='lightblue')
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 99, 99], outline='black')
    draw.text((35, 40), f"Casino {number}", fill='black')
    return image

def create_money_image():
    image = Image.new('RGB', (30, 20), color='lightgreen')
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 29, 19], outline='black')
    draw.text((10, 5), "$", fill='black')
    return image

def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def main():
    st.title("라스베가스 게임")
    st.write("""
        ##### 게임 설명
        - 라스베가스 게임은 주사위를 굴려 카지노에 배치하고 돈을 획득하는 게임입니다. 
        - 각 플레이어는 일반 주사위 8개 와 딜러 주사위 4개를 사용하여 카지노에 배치할 수 있습니다. 
        - 라운드가 끝나면 각 카지노에서 가장 많은 주사위를 배치한 플레이어가 돈을 획득합니다. 
        - 딜러 주사위는 통합 주사위로 딜러 주사위를 이용해서 상대방의 주사위를 막을 수 있습니다.
        - 4라운드가 끝난 후 가장 많은 돈을 가진 플레이어가 승리합니다.
        """)
    if 'game' not in st.session_state:
        st.session_state.game = None
        st.session_state.round_ended = False

    if st.session_state.game is None:
        num_players = st.selectbox("플레이어 수 선택:", options=[2, 3, 4, 5])
        if st.button("게임 시작"):
            st.session_state.game = VegasGame(num_players)
            st.rerun()

    else:
        game = st.session_state.game
        
        st.write(f"라운드: {game.current_round}, 현재 플레이어: {game.current_player + 1}")
        current_player = game.players[game.current_player]
        st.write(f"남은 일반 주사위: {current_player.dice}, 남은 딜러 주사위: {current_player.dealer_dice}")

        a, b = st.columns(2)
        with a:
            cols = st.columns(3)
            for i, casino in enumerate(game.casinos):
                with cols[i % 3]:
                    st.image(image_to_bytes(create_casino_image(casino.number)))
                    money_str = ", ".join([f"${m}" for m in casino.money])
                    st.image(image_to_bytes(create_money_image()))
                    st.write(f"돈: {money_str}")
                    dice_str = ", ".join([f"P{p+1}: {c}" for p, c in casino.dice.items()])
                    st.write(f"주사위: {dice_str}")
                    st.write(f"딜러 주사위: {casino.dealer_dice}")
        with b:
            st.write("플레이어 돈:")
            for player in game.players:
                st.write(f"플레이어 {player.id + 1}: ${player.money}")

            if st.button("주사위 굴리기"):
                if not game.dice_rolled:
                    if game.play_round():
                        st.rerun()
                else:
                    st.warning("이미 주사위를 굴렸습니다. 주사위를 배치해주세요.")

            dice_count = current_player.get_dice_count()
            dealer_dice_count = current_player.get_dealer_dice_count()
            
            st.write("일반 주사위:")
            cols = st.columns(6)
            for i in range(6):
                with cols[i]:
                    st.image(image_to_bytes(create_dice_image(i+1)))
                    st.write(f"{i+1}: {dice_count[i+1]}")
            
            st.write("딜러 주사위:")
            cols = st.columns(6)
            for i in range(6):
                with cols[i]:
                    st.image(image_to_bytes(create_dealer_dice_image(i+1)))
                    st.write(f"{i+1}: {dealer_dice_count[i+1]}")

            available_dice = sorted(set(current_player.current_roll + current_player.current_dealer_roll))
            dice_choice = st.selectbox("배치할 주사위 선택 (카지노 번호와 동일):", options=available_dice)
            
            regular_count = current_player.current_roll.count(dice_choice)
            dealer_count = current_player.current_dealer_roll.count(dice_choice)
            
            st.write(f"선택한 주사위 {dice_choice}의 개수: 일반 주사위 {regular_count}개, 딜러 주사위 {dealer_count}개")
            
            if st.button("주사위 배치"):
                if game.place_dice(dice_choice):
                    if all(player.dice == 0 and player.dealer_dice == 0 for player in game.players):
                        st.session_state.round_ended = True
                    st.rerun()

            if st.session_state.round_ended:
                winnings = game.end_round()
                st.write("라운드 결과:")
                for player_id, player_winnings in winnings.items():
                    player = game.players[player_id]
                    st.write(f"플레이어 {player_id + 1}:")
                    for casino_number, amount in player_winnings:
                        if amount > 0:
                            st.write(f"  카지노 {casino_number}에서 ${amount} 획득")
                    st.write(f"  총 잔액: ${player.money}")
                
                st.session_state.round_ended = False
                
                if game.current_round == 5:
                    winner = game.get_winner()
                    st.write(f"게임 종료! 승자: 플레이어 {winner.id + 1} (${winner.money}, 카드 {winner.card_count}장)")
                    if st.button("새 게임 시작"):
                        st.session_state.game = None
                        st.rerun()
                else:
                    if st.button("다음 라운드 시작"):
                        st.rerun()

if __name__ == "__main__":
    main()
