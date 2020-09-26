# coding: utf-8

from numpy.random import choice
from enum import Enum


def load_const_from_file(filename, func):
    with open(filename, "r") as f:
        contents = ",".join(f.readlines()).split(",")
        contents = [c.strip() for c in contents]
        contents = [func(c) for c in contents if len(c) > 0]
    return contents


# TODO: 気が向いたら設定ファイルを作って一括で読み込む

BOOSTUP_COUNT_DROP = load_const_from_file("data/boostup_count_drop.txt", int)
BOOSTUP_COUNT_POINT = load_const_from_file("data/boostup_count_point.txt", int)
BOOSTUP_COUNT_APPEAL = load_const_from_file("data/boostup_count_appeal.txt", int)
BOOSTUP_COUNT_DATE = load_const_from_file("data/boostup_count_date.txt", int)

BOOSTUP_RATE_DROP = load_const_from_file("data/boostup_rate_drop.txt", float)
BOOSTUP_RATE_POINT = load_const_from_file("data/boostup_rate_point.txt", float)
BOOSTUP_RATE_APPEAL = load_const_from_file("data/boostup_rate_appeal.txt", float)
BOOSTUP_RATE_DATE = load_const_from_file("data/boostup_rate_date.txt", float)

# TODO: 経験値ボーナスの計算をする（現状ボーナスついたものなので）
ATTACK1_HP = load_const_from_file("data/attack1_hp.txt", int)
ATTACK1_EXP = load_const_from_file("data/attack1_exp.txt", int)
ATTACK3_HP = load_const_from_file("data/attack3_hp.txt", int)
ATTACK3_EXP = load_const_from_file("data/attack3_exp.txt", int)
ATTACK5_HP = load_const_from_file("data/attack5_hp.txt", int)
ATTACK5_EXP = load_const_from_file("data/attack5_exp.txt", int)
ATTACKSP_HP = load_const_from_file("data/attacksp_hp.txt", int)
ATTACKSP_EXP = load_const_from_file("data/attacksp_exp.txt", int)

# TODO: 好感度の内部数値推測
LOVE_APPEAL_COUNT = [20] * 10 + [30] * 10 + [40] * 10 + [45] * 10 + [50] * 10 + [30]


RUN_STAMINA = 2


# TODO: 戦略の組み立て可能ロジック
# TODO: choiceのラップ化？
# TODO: 獲得ポイントの乱数化


class ItemManager:
    def __init__(self, boostup_count, boostup_rate, love_appeal, love_appeal_rate):
        self.boostup_count = boostup_count
        self.boostup_rate = boostup_rate
        self.current_num = 0
        self.current_boost = 0.0
        self.love_appeal = love_appeal
        self.love_appeal_rate = love_appeal_rate

    def get(self, num):
        self.current_num += num
        self.love_appeal.get(num * self.love_appeal_rate)
        current_num = self.current_num
        for c, r in zip(self.boostup_count, self.boostup_rate):
            current_num -= c
            self.current_boost = r
            if current_num < 0:
                break

    def boost(self):
        return self.current_boost

    def is_max(self):
        return self.boostup_rate[-1] == self.current_boost


# TODO: 好感度に基づくアイテム処理
class LoveAppeal:
    def __init__(self, love_appeal_count):
        self.love_appeal_count = love_appeal_count
        self.love_level = 1
        self.love_power = 0

    def get(self, up):
        self.love_power += up
        love_max = len(self.love_appeal_count)
        while self.love_power >= self.love_appeal_count[min(self.love_level, love_max) - 1]:
            self.love_power -= self.love_appeal_count[min(self.love_level, love_max) - 1]
            self.love_level += 1


# TODO: staminaは経験値とかレベルとかをまとめて管理するべき(BPは？)
class Stamina:
    # TODO: max処理
    def __init__(self, stamina, charge_half, charge, level):
        self.stamina = stamina
        self.charge = charge_half + charge * 2
        self.level = level
        assert level == 150, "now only support level 150"

    def run(self, st):
        if self.stamina < st:
            if self.charge > 0:
                self.charge -= 1
                self.stamina += 107  # TODO: levelに応じて変化量変更
            else:
                raise ValueError("no stamina and item")

        self.stamina -= st

    def recover(self, st):
        self.stamina += st

    def is_end(self, st):
        return self.charge == 0 and self.stamina < st


class BP:
    # TODO: max処理
    def __init__(self, bp, candy_mini, candy):
        self.bp = bp
        self.candy = candy_mini + candy * 5

    def run(self, bp):
        if self.bp < bp:
            if self.candy >= bp:
                self.candy -= bp
                self.bp += bp
            else:
                raise ValueError("no bp and item")

        self.bp -= bp

    def can_attack(self, bp):
        return self.bp + self.candy >= bp

    def recover(self, bp):
        self.bp += bp

    def is_end(self):
        return self.bp == 0 and self.candy == 0


class SpecialBP:
    def __init__(self, special):
        self.special = special

    def run(self):
        if self.special > 0:
            self.special -= 1
            return
        raise ValueError("no special item")

    def can_attack(self):
        return self.special > 0

    def is_end(self):
        return self.special == 0


class EnemyType(Enum):
    ENEMY1 = 1
    ENEMY3 = 3
    ENEMY5 = 5
    ENEMY7 = 7


class EnemyManager:
    def __init__(self, hps, exps, bp, special, enemy_type, random=False):
        self.current_level = 1
        self.hps = hps
        self.exps = exps
        self.bp = bp
        self.special = special
        self.enemy_type = enemy_type
        self.random = random

        if len(hps) != len(exps):
            raise ValueError("hps and exps should be same length")
        self.max_level = len(hps)

    def get(self):
        if self.random:
            level = choice(range(self.max_level), 1)[0]
        else:
            level = self.current_level - 1
        return Enemy(self.hps[level], self.exps[level], self, self.bp, self.special, self.enemy_type,)

    def win(self):
        if not self.random:
            self.current_level = min(self.current_level + 1, self.max_level)


class AttackType(Enum):
    ATTACK1 = 1
    ATTACK3 = 3
    ATTACKSP = 10


class Enemy:
    def __init__(self, hp, exp, manager, bp, special, enemy_type):
        self.hp = hp
        self.exp = exp
        self.manager = manager
        self.bp = bp
        self.special = special
        self.enemy_type = enemy_type

    def is_win(self):
        return self.hp <= 0

    # return: 獲得経験値，アイテム数
    def attack(self, drop_rate, appeal, point, attack_type):
        if self.is_win():
            raise ValueError("enemy is already deleted")

        twice = choice([1, 2], 1, [0.7, 0.3])[0]

        if attack_type == AttackType.ATTACK1 and self.bp.can_attack(1):
            attack1 = appeal.boost()
            self.bp.run(1)
            self.hp -= attack1 * twice

        if attack_type == AttackType.ATTACK3 and self.bp.can_attack(3):
            attack3 = appeal.boost() * 4
            self.bp.run(3)
            self.hp -= attack3 * twice

        if attack_type == AttackType.ATTACKSP and self.special.can_attack():
            attacksp = appeal.boost() * 10
            self.special.run()
            self.hp -= attacksp * twice

        if self.hp > 0:
            return 0, 0
        else:
            self.manager.win()
            return (
                self.exp * point.boost(),
                choice(range(len(drop_rate)), 1, drop_rate)[0],
            )


class DateManager:
    def __init__(self, enemy5, enemy7, item_manager):
        self.date = 0
        self.enemy1count = 0
        self.enemy3count = 0
        self.enemy = None
        self.enemy5 = enemy5
        self.enemy7 = enemy7
        self.item_manager = item_manager

    def is_end(self):
        return self.date == 0 and self.enemy is None

    def update(self, enemy_type):
        if enemy_type == EnemyType.ENEMY1:
            self.enemy1count += 1
        elif enemy_type == EnemyType.ENEMY3:
            self.enemy3count += 1
        else:
            raise ValueError("invalid type")

        if self.enemy1count >= 3 and self.enemy3count >= 1:
            self.date += 1
            self.enemy1count -= 3
            self.enemy3count -= 1

    def get(self):
        return self.enemy

    def attack(self, drop_rate, appeal, point, attack_type, god_rate):
        if self.date > 0 and self.enemy is None:
            self.date -= 1
            self.enemy = self.enemy5.get()

        if self.enemy is None:
            raise ValueError("no date")

        point, item = self.enemy.attack(drop_rate, appeal, point, attack_type)

        if self.enemy.is_win():
            self.enemy = None
            self.item_manager.get(item)
            god = choice([False, True], 1, [1 - god_rate, god_rate])[0]
            if god:
                self.enemy = self.enemy7.get()

        return point


class BoostManager:
    # boost_listには boostメソッドを実装していること
    def __init__(self, base_appeal, boost_list=[]):
        self.base_appeal = base_appeal
        self.boost_list = boost_list

    def boost(self):
        boost_sum = sum([b.boost() for b in self.boost_list]) + 1.0
        return int(boost_sum * self.base_appeal)


class ConstBoost:
    def __init__(self, appeal):
        self.appeal = appeal

    def boost(self):
        return self.appeal


class DropRate:
    def __init__(self, drop_rate):
        self.drop_rate = drop_rate

    def get(self, rate):
        s = sum(self.drop_rate)
        drop_rate = [rate * dr / s for dr in self.drop_rate]
        return [1 - rate] + drop_rate


class Stage:
    def __init__(
        self, stamina, bp, special, enemy_manager1, enemy_manager3, date_manager, item_manager,
    ):
        self.enemy = None
        self.stamina = stamina
        self.bp = bp
        self.special = special
        self.enemy_manager1 = enemy_manager1
        self.enemy_manager3 = enemy_manager3
        self.date_manager = date_manager
        self.item_manager = item_manager

    def run(self, appeal, point, drop_rate):
        self.stamina.run(RUN_STAMINA)

        def enemy():
            if self.enemy is None:
                self.enemy = choice([self.enemy_manager1, self.enemy_manager3], 1, [0.75, 0.25])[0].get()

        def recover():
            self.bp.recover(choice([1, 2, 3], 1, [0.70, 0.20, 0.10])[0])

        def heart():
            pass

        def noop():
            pass

        choice([noop, enemy, recover, heart], 1, [0.25, 0.50, 0.10, 0.15])[0]()

        total_point = 35

        if self.enemy is not None and self.bp.can_attack(1):
            p, item = self.enemy.attack(drop_rate, appeal, point, AttackType.ATTACK1)
            total_point += p
            if self.enemy.is_win():
                self.item_manager.get(item)
                self.date_manager.update(self.enemy.enemy_type)
                self.enemy = None

        return total_point


# TODO: ガチャによるappealアップ実装
# TODO: メンバーをどのアタックタイプで倒すかの選択
class Simulator:
    def __init__(self, *, appeal, bp, stamina, special):
        self.appeal = appeal
        self.stamina = stamina
        self.bp = bp
        self.special = special

        self.enemy1 = EnemyManager(ATTACK1_HP, ATTACK1_EXP, self.bp, self.special, EnemyType.ENEMY1, random=False,)
        self.enemy3 = EnemyManager(ATTACK3_HP, ATTACK3_EXP, self.bp, self.special, EnemyType.ENEMY3, random=False,)
        self.enemy5 = EnemyManager(ATTACK5_HP, ATTACK5_EXP, self.bp, self.special, EnemyType.ENEMY5, random=True,)
        self.enemy7 = EnemyManager(ATTACKSP_HP, ATTACKSP_EXP, self.bp, self.special, EnemyType.ENEMY7, random=False,)

        self.love_appeal = LoveAppeal(LOVE_APPEAL_COUNT)

        self.dropup = ItemManager(BOOSTUP_COUNT_DROP, BOOSTUP_RATE_DROP, self.love_appeal, 1)
        self.pointup = ItemManager(BOOSTUP_COUNT_POINT, BOOSTUP_RATE_POINT, self.love_appeal, 2)
        self.appealup = ItemManager(BOOSTUP_COUNT_APPEAL, BOOSTUP_RATE_APPEAL, self.love_appeal, 3)
        self.dateup = ItemManager(BOOSTUP_COUNT_DATE, BOOSTUP_RATE_DATE, self.love_appeal, 5)

        self.date_manager = DateManager(self.enemy5, self.enemy7, self.dateup)
        self.stage1 = Stage(
            self.stamina, self.bp, self.special, self.enemy1, self.enemy3, self.date_manager, self.dropup,
        )
        self.stage2 = Stage(
            self.stamina, self.bp, self.special, self.enemy1, self.enemy3, self.date_manager, self.pointup,
        )
        self.stage3 = Stage(
            self.stamina, self.bp, self.special, self.enemy1, self.enemy3, self.date_manager, self.appealup,
        )

        self.drop_rate = DropRate([3, 2, 1])

    def simulate_score(self, card_appeal=0.0, card_point=0.0):
        total_point = 0
        appeal = BoostManager(self.appeal, [self.appealup, ConstBoost(card_appeal)])
        point = BoostManager(1.0, [self.pointup, ConstBoost(card_point)])  # FIXME: これはナンセンスでは？

        while not (
            self.stamina.is_end(RUN_STAMINA)
            and ((self.bp.is_end() and self.special.is_end()) or self.date_manager.is_end())
        ):

            if not self.stamina.is_end(RUN_STAMINA):
                love_level = self.love_appeal.love_level
                stages = [self.stage1]
                is_maxs = [self.dropup.is_max()]
                if love_level >= 10:
                    stages.append(self.stage2)
                    is_maxs.append(self.pointup.is_max())
                if love_level >= 20:
                    stages.append(self.stage3)
                    is_maxs.append(self.appealup.is_max())

                stage = None
                for s, m in zip(stages, is_maxs):
                    if not m:
                        stage = s
                        break

                if stage is None:
                    stage = stages[-1]

                p = stage.run(appeal, point, self.drop_rate.get(0.3 * self.dropup.boost()))
                total_point += p
            elif not (self.bp.is_end() and self.special.is_end()) and not self.date_manager.is_end():
                p = self.date_manager.attack(
                    self.drop_rate.get(0.3 * self.dropup.boost()),
                    appeal,
                    point,
                    AttackType.ATTACK1,
                    0.45 * self.dateup.boost(),
                )

                total_point += p
        return total_point


if __name__ == "__main__":
    # BP(自然回復分，ミニキャンディ，キャンディ)
    bp = BP(0, 1000, 1000)

    # Stamina(自然回復分，チャージハーフ，チャージフル，レベル)
    stamina = Stamina(0, 1000, 0, 150)

    # 鈍器
    special = SpecialBP(0)

    # アピール値 (BP1の値)
    simulator = Simulator(appeal=13000, bp=bp, stamina=stamina, special=special)
    print(simulator.simulate_score())
