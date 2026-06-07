from unittest.mock import patch, MagicMock
from models.player import Player
from systems.achievements import AchievementsManager
from systems.longest_road import calculate_longest_road
from core.trade import BankTrade, PlayerTrade, TradeOffer
from components.port import Port
from constants.types import ROCK, TREE, LAMB, BRICK, WHEAT, GENERIC
from constants.colors import RED, BLUE, GREEN


def test_longest_road_calculation():
    player = Player(1, "Alice", RED)
    
    # Mock de casas
    class MockHouse:
        def __init__(self, owner=None):
            self.owner = owner
    
    # Mock de estradas conectadas
    class MockRoad:
        def __init__(self, house_a, house_b, owner):
            self.house_a = house_a
            self.house_b = house_b
            self.owner = owner
    
    # Criar cadeia: H1 - H2 - H3 - H4 - H5 (4 estradas)
    houses = [MockHouse() for _ in range(5)]
    roads = [
        MockRoad(houses[0], houses[1], player),
        MockRoad(houses[1], houses[2], player),
        MockRoad(houses[2], houses[3], player),
        MockRoad(houses[3], houses[4], player),
    ]
    
    length = calculate_longest_road(player, roads)
    assert length == 4, f"Estrada deve ter 4 segmentos, mas retornou {length}"


def test_longest_road_with_blocks():
    player1 = Player(1, "Alice", RED)
    player2 = Player(2, "Bob", BLUE)
    
    class MockHouse:
        def __init__(self, owner=None):
            self.owner = owner
    
    class MockRoad:
        def __init__(self, house_a, house_b, owner):
            self.house_a = house_a
            self.house_b = house_b
            self.owner = owner
    
    # H1(empty) - H2(empty) [player1] - H3(player2, bloqueio) - H4(empty) [player1]
    h1 = MockHouse()
    h2 = MockHouse()
    h3 = MockHouse(owner=player2)
    h4 = MockHouse()
    
    roads = [
        MockRoad(h1, h2, player1),
        MockRoad(h2, h3, player1),
        MockRoad(h3, h4, player1),
    ]
    
    length = calculate_longest_road(player1, roads)
    assert length <= 1, f"Estrada deve parar no bloqueio, mas retornou {length}"


def test_longest_road_transfer_between_players():
    p1 = Player(1, "Alice", RED)
    p2 = Player(2, "Bob", BLUE)
    
    class MockHouse:
        def __init__(self, owner=None):
            self.owner = owner
    
    class MockRoad:
        def __init__(self, house_a, house_b, owner):
            self.house_a = house_a
            self.house_b = house_b
            self.owner = owner
    
    manager = AchievementsManager([p1, p2])
    
    # P1 com 5 estradas
    roads_p1 = [
        MockRoad(MockHouse(), MockHouse(), p1),
        MockRoad(MockHouse(), MockHouse(), p1),
        MockRoad(MockHouse(), MockHouse(), p1),
        MockRoad(MockHouse(), MockHouse(), p1),
        MockRoad(MockHouse(), MockHouse(), p1),
    ]
    
    # P2 com 3 estradas
    roads_p2 = [
        MockRoad(MockHouse(), MockHouse(), p2),
        MockRoad(MockHouse(), MockHouse(), p2),
        MockRoad(MockHouse(), MockHouse(), p2),
    ]
    
    all_roads = roads_p1 + roads_p2
    
    # Mock calculate_longest_road
    with patch('systems.achievements.calculate_longest_road') as mock_calc:
        def side_effect(player, roads):
            if player == p1:
                return 5
            elif player == p2:
                return 3
            return 0
        
        mock_calc.side_effect = side_effect
        manager.update_longest_road(all_roads)
    
    assert p1.has_longest_road == True, "P1 deve ter longest_road (5 vs 3)"
    assert p2.has_longest_road == False, "P2 não deve ter longest_road"
    
    # P2 constrói para 6
    roads_p2_extended = roads_p2 + [
        MockRoad(MockHouse(), MockHouse(), p2),
    ]
    all_roads = roads_p1 + roads_p2_extended
    
    with patch('systems.achievements.calculate_longest_road') as mock_calc:
        def side_effect_2(player, roads):
            if player == p1:
                return 5
            elif player == p2:
                return 6
            return 0
        
        mock_calc.side_effect = side_effect_2
        manager.update_longest_road(all_roads)
    
    assert p1.has_longest_road == False, "P1 não deve ter longest_road (transferido)"
    assert p2.has_longest_road == True, "P2 deve ter longest_road (6 > 5)"


def test_longest_road_bonus_in_victory_points():
    p1 = Player(1, "Alice", RED)
    p1.settlements_count = 3
    p1.has_longest_road = True
    
    p2 = Player(2, "Bob", BLUE)
    p2.settlements_count = 5
    p2.has_longest_road = False
    
    vp_p1 = p1.victory_points
    vp_p2 = p2.victory_points
    
    assert vp_p1 == 5, f"P1 deve ter 5 pts (3 aldeias + 2 bonus), mas tem {vp_p1}"
    assert vp_p2 == 5, f"P2 deve ter 5 pts (5 aldeias), mas tem {vp_p2}"


def test_largest_army_transfer():

    p1 = Player(1, "Alice", RED)
    p1.knights_played = 3
    
    p2 = Player(2, "Bob", BLUE)
    p2.knights_played = 2
    
    manager = AchievementsManager([p1, p2])
    manager.update_largest_army()
    
    assert p1.has_largest_army == True, "P1 deve ter largest_army (3 vs 2)"
    
    # P2 joga 3ª (empate)
    p2.knights_played = 3
    manager.update_largest_army()
    
    # Em empate, P1 mantém ou P2 ganha? (Implementação define)
    # Teste apenas valida coerência
    total_army = sum([p1.has_largest_army, p2.has_largest_army])
    assert total_army <= 1, "No máximo 1 player tem largest_army"


def test_bank_trade_without_ports():
    player = Player(1, "Alice", RED)
    player.inventory.add(BRICK, 4)
    
    # Sem portos
    ports = []
    
    ratio = BankTrade.get_ratio(player, BRICK, ports)
    assert ratio == 4, f"Sem porto, ratio deve ser 4, mas é {ratio}"
    
    # Validar trade
    can_do = BankTrade.can_execute(player, BRICK, 4, WHEAT, ports)
    assert can_do, "Deve conseguir trocar 4 BRICK por 1 WHEAT"
    
    # Executar
    success = BankTrade.execute(player, BRICK, 4, WHEAT)
    assert success, "Trade deve ser executado com sucesso"
    assert player.inventory.get_count(BRICK) == 0, "BRICK deve ser removido"
    assert player.inventory.get_count(WHEAT) == 1, "WHEAT deve ser adicionado"


def test_bank_trade_with_generic_port():
    player = Player(1, "Alice", RED)
    player.inventory.add(BRICK, 3)
    
    # Mock porto genérico
    port_house1 = MagicMock(owner=player)
    port_house2 = MagicMock(owner=None)
    generic_port = MagicMock(
        house1=port_house1,
        house2=port_house2,
        type=GENERIC,
        ratio=3
    )
    ports = [generic_port]
    
    ratio = BankTrade.get_ratio(player, BRICK, ports)
    assert ratio == 3, f"Com porto genérico, ratio deve ser 3, mas é {ratio}"
    
    can_do = BankTrade.can_execute(player, BRICK, 3, WHEAT, ports)
    assert can_do, "Deve conseguir trocar 3 BRICK por 1 WHEAT"
    
    success = BankTrade.execute(player, BRICK, 3, WHEAT)
    assert success
    assert player.inventory.get_count(BRICK) == 0
    assert player.inventory.get_count(WHEAT) == 1


def test_bank_trade_with_specific_port():
    player = Player(1, "Alice", RED)
    player.inventory.add(BRICK, 2)
    player.inventory.add(TREE, 5)
    
    # Porto específico para BRICK
    port_house1 = MagicMock(owner=player)
    port_house2 = MagicMock(owner=None)
    brick_port = MagicMock(
        house1=port_house1,
        house2=port_house2,
        type=BRICK,
        ratio=2
    )
    
    # Porto genérico
    generic_port = MagicMock(
        house1=port_house1,
        house2=port_house2,
        type=GENERIC,
        ratio=3
    )
    
    ports = [brick_port, generic_port]
    
    # BRICK deve usar 2:1 (específico é melhor que genérico)
    ratio_brick = BankTrade.get_ratio(player, BRICK, ports)
    assert ratio_brick == 2, f"BRICK com porto específico deve ser 2, mas é {ratio_brick}"
    
    # TREE deve usar 3:1 (genérico, sem específico)
    ratio_tree = BankTrade.get_ratio(player, TREE, ports)
    assert ratio_tree == 3, f"TREE sem porto específico deve ser 3, mas é {ratio_tree}"


def test_bank_trade_without_port_ownership():
    player = Player(1, "Alice", RED)
    player.inventory.add(BRICK, 2)
    
    # Porto que player não possui
    port_house1 = MagicMock(owner=None)  # Owner diferente
    port_house2 = MagicMock(owner=None)
    brick_port = MagicMock(
        house1=port_house1,
        house2=port_house2,
        type=BRICK,
        ratio=2
    )
    
    ports = [brick_port]
    
    ratio = BankTrade.get_ratio(player, BRICK, ports)
    assert ratio == 4, f"Sem porto, ratio deve ser 4, mas é {ratio}"


def test_player_trade_proposal():
    p1 = Player(1, "Alice", RED)
    p1.inventory.add(BRICK, 2)
    
    p2 = Player(2, "Bob", BLUE)
    p2.inventory.add(WHEAT, 1)
    
    offer = TradeOffer(p1, p2, {BRICK: 2}, {WHEAT: 1})
    
    can_propose = PlayerTrade.can_propose(offer)
    assert can_propose, "P1 deve poder propor (tem BRICK)"
    
    can_accept = PlayerTrade.can_accept(offer)
    assert can_accept, "P2 deve poder aceitar (tem WHEAT)"
    
    success = PlayerTrade.execute(offer)
    assert success, "Trade deve executar com sucesso"
    
    assert p1.inventory.get_count(BRICK) == 0, "P1 deve perder BRICK"
    assert p1.inventory.get_count(WHEAT) == 1, "P1 deve ganhar WHEAT"
    assert p2.inventory.get_count(BRICK) == 2, "P2 deve ganhar BRICK"
    assert p2.inventory.get_count(WHEAT) == 0, "P2 deve perder WHEAT"


def test_player_trade_failure_insufficient_resources():
    p1 = Player(1, "Alice", RED)
    p1.inventory.add(BRICK, 2)  # Menos que o oferecido
    
    p2 = Player(2, "Bob", BLUE)
    p2.inventory.add(WHEAT, 1)
    
    offer = TradeOffer(p1, p2, {BRICK: 5}, {WHEAT: 1})
    
    can_propose = PlayerTrade.can_propose(offer)
    assert not can_propose, "P1 não deve poder propor (falta BRICK)"
    
    success = PlayerTrade.execute(offer)
    assert not success, "Trade não deve executar sem recursos"
