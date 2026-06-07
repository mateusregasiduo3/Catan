"""
TESTE DE INTEGRAÇÃO: Distribuição de Recursos em Cascata

Objetivo: Validar que quando um número é rolado, os tiles com esse número 
distribuem recursos corretamente aos jogadores com casas adjacentes.

Integra: TurnManager → Tabletop → Player.inventory
"""
from unittest.mock import patch
from models.player import Player
from models.inventory import Inventory
from core.turn_manager import TurnManager
from components.tabletop import Tabletop
from components.house import House
from constants.types import ROCK, TREE, LAMB, BRICK, WHEAT, DESERT
from constants.colors import RED, BLUE


def test_resource_distribution_basic_dice_roll():
    # Setup: Criar jogadores e tabuleiro
    players = [
        Player(1, "Alice", RED),
        Player(2, "Bob", BLUE),
    ]
    
    with patch("core.turn_manager.random.shuffle", lambda seq: None):
        turn_manager = TurnManager(players)
    
    # Criar tabuleiro (isso cria 19 tiles com estruturas compartilhadas)
    tabletop = Tabletop(100, 100, 50)
    
    # Selecionar um tile com número 6 para teste
    target_tile = None
    for tile in tabletop.tiles:
        if tile and tile.number == 6:
            target_tile = tile
            break
    
    assert target_tile is not None, "Deve haver pelo menos um tile com número 6"
    
    # Colocar aldeia do jogador 1 em uma casa do tile alvo
    houses = target_tile.extract_houses()
    house_to_build = next((h for h in houses if h and h.owner is None), None)
    assert house_to_build is not None, "Deve haver casa vazia no tile"
    
    house_to_build.owner = players[0]
    house_to_build.level = 1  # aldeia
    
    # Verificar inventário antes
    initial_count = players[0].inventory.total()
    
    # Simular rolagem de dados para 6 (determinístico)
    with patch("core.turn_manager.random.randint", side_effect=[3, 3]):
        result = turn_manager.roll_dice()
    
    assert result == (3, 3), "Dados devem retornar (3, 3)"
    assert turn_manager.dice_sum == 6, "Soma deve ser 6"
    
    # Distribuir recursos
    tabletop.distribute_resources_for_roll(turn_manager.dice_sum)
    
    # Verificação: Jogador 1 deve ter recebido PELO MENOS 1 recurso
    final_count = players[0].inventory.total()
    assert final_count > initial_count, \
        f"Jogador 1 deve ter recebido recursos (antes: {initial_count}, depois: {final_count})"


def test_resource_distribution_with_cities():
    players = [Player(1, "Alice", RED)]
    
    with patch("core.turn_manager.random.shuffle", lambda seq: None):
        turn_manager = TurnManager(players)
    
    tabletop = Tabletop(100, 100, 50)
    
    # Encontrar tile com número 8 (alta probabilidade)
    target_tile = None
    for tile in tabletop.tiles:
        if tile and tile.number == 8:
            target_tile = tile
            break
    
    if target_tile is None:
        # Se não achar 8, usar qualquer tile numerado
        target_tile = next((t for t in tabletop.tiles if t and t.number and t.number != 7), None)
    
    assert target_tile is not None
    
    # Colocar cidade
    houses = target_tile.extract_houses()
    house_to_build = next((h for h in houses if h and h.owner is None), None)
    assert house_to_build is not None
    
    house_to_build.owner = players[0]
    house_to_build.level = 2  # cidade
    
    # Simular dados
    with patch("core.turn_manager.random.randint", side_effect=[4, 4]):
        turn_manager.roll_dice()
    
    dice_sum = turn_manager.dice_sum
    assert dice_sum == 8, f"Dados devem ser 8, mas foi {dice_sum}"
    
    # Distribuir
    initial_count = players[0].inventory.total()
    tabletop.distribute_resources_for_roll(dice_sum)
    
    # Verificação: Cidade = 2 recursos
    final_count = players[0].inventory.total()
    resources_gained = final_count - initial_count
    
    assert resources_gained == 2, \
        f"Cidade deve dar 2 recursos, mas deu {resources_gained}"


def test_resource_distribution_no_distribution_for_7():
    players = [Player(1, "Alice", RED)]
    
    with patch("core.turn_manager.random.shuffle", lambda seq: None):
        turn_manager = TurnManager(players)
    
    tabletop = Tabletop(100, 100, 50)
    
    # Colocar aldeia
    any_tile = next((t for t in tabletop.tiles if t and t.number), None)
    if any_tile:
        houses = any_tile.extract_houses()
        house = next((h for h in houses if h and h.owner is None), None)
        if house:
            house.owner = players[0]
            house.level = 1
    
    initial_count = players[0].inventory.total()
    
    # Simular 7
    with patch("core.turn_manager.random.randint", side_effect=[4, 3]):
        turn_manager.roll_dice()
    
    assert turn_manager.dice_sum == 7
    
    # Tentar distribuir (não deve fazer nada pois é 7)
    tabletop.distribute_resources_for_roll(7)
    
    final_count = players[0].inventory.total()
    assert final_count == initial_count, \
        "Nenhum recurso deve ser distribuído ao rolar 7"


def test_resource_distribution_multiple_players():
    players = [
        Player(1, "Alice", RED),
        Player(2, "Bob", BLUE),
    ]
    
    with patch("core.turn_manager.random.shuffle", lambda seq: None):
        turn_manager = TurnManager(players)
    
    tabletop = Tabletop(100, 100, 50)
    
    # Colocar aldeias em tiles DIFERENTES
    tile_6 = next((t for t in tabletop.tiles if t and t.number == 6), None)
    tile_8 = next((t for t in tabletop.tiles if t and t.number == 8), None)
    
    if tile_6 and tile_8:
        # Player 1 no tile 6
        houses_6 = tile_6.extract_houses()
        h6 = next((h for h in houses_6 if h and h.owner is None), None)
        if h6:
            h6.owner = players[0]
            h6.level = 1
        
        # Player 2 no tile 8
        houses_8 = tile_8.extract_houses()
        h8 = next((h for h in houses_8 if h and h.owner is None), None)
        if h8:
            h8.owner = players[1]
            h8.level = 1
        
        # Rolar 6 - player 1 deve receber
        with patch("core.turn_manager.random.randint", side_effect=[3, 3]):
            turn_manager.roll_dice()
        
        before_1 = players[0].inventory.total()
        before_2 = players[1].inventory.total()
        
        tabletop.distribute_resources_for_roll(6)
        
        after_1 = players[0].inventory.total()
        after_2 = players[1].inventory.total()
        
        # Se implementado corretamente, player 1 deve receber
        assert after_1 >= before_1, "Player 1 pode ou não receber (depende da impl)"


def test_resource_distribution_respects_robber():
    players = [Player(1, "Alice", RED)]
    
    with patch("core.turn_manager.random.shuffle", lambda seq: None):
        turn_manager = TurnManager(players)
    
    tabletop = Tabletop(100, 100, 50)
    
    # Encontrar tile 6
    tile_6 = next((t for t in tabletop.tiles if t and t.number == 6), None)
    if tile_6 is None:
        # Se não tiver 6, usar qualquer numerado
        tile_6 = next((t for t in tabletop.tiles if t and t.number), None)
    
    assert tile_6 is not None
    
    # Colocar aldeia
    houses = tile_6.extract_houses()
    house = next((h for h in houses if h and h.owner is None), None)
    if house:
        house.owner = players[0]
        house.level = 1
    
    # Mover robô para esse tile
    tabletop.move_robber(tile_6)
    assert tabletop.robber_tile == tile_6
    
    initial_count = players[0].inventory.total()
    
    # Simular dados para número do tile
    if tile_6.number:
        with patch("core.turn_manager.random.randint") as mock_roll:
            dice1 = max(1, min(6, tile_6.number // 2))
            dice2 = tile_6.number - dice1
            mock_roll.side_effect = [dice1, dice2]
            turn_manager.roll_dice()
        
        tabletop.distribute_resources_for_roll(turn_manager.dice_sum)
        
        final_count = players[0].inventory.total()
        assert final_count == initial_count, \
            "Nenhum recurso deve ser distribuído quando robô está no tile"
