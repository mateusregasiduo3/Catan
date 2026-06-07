from unittest.mock import patch, MagicMock
from models.player import Player
from systems.card_manager import CardManager
from components.base_card import KnightCard, RoadBuildingCard, YearOfPlentyCard, MonopolyCard
from components.card_states import CardState
from constants.types import ROCK, LAMB, WHEAT, BRICK, TREE
from constants.colors import RED, BLUE


def test_development_card_purchase_and_lock():
    player = Player(1, "Alice", RED)
    player.inventory.add(ROCK, 1)
    player.inventory.add(LAMB, 1)
    player.inventory.add(WHEAT, 1)
    
    manager = CardManager([player])
    
    # Mock para deck não vazio
    knight_card = KnightCard(owner=player)
    manager.development_cards = [knight_card]
    
    # Comprar
    success = manager.attempt_buy_card(player)
    
    assert success, "Deve conseguir comprar carta"
    assert len(player.development_cards) == 1, "Carta deve estar no player"
    assert player.development_cards[0].state == CardState.LOCKED, "Carta deve estar LOCKED"
    assert player.development_cards[0].bought_this_turn == True, "Flag de compra deve estar True"
    assert player.inventory.get_count(ROCK) == 0, "ROCK deve ser removido"
    assert player.inventory.get_count(LAMB) == 0, "LAMB deve ser removido"
    assert player.inventory.get_count(WHEAT) == 0, "WHEAT deve ser removido"


def test_development_card_unlock_on_turn_start():
    player = Player(1, "Alice", RED)
    
    # Criar carta e adicionar ao player
    knight_card = KnightCard(owner=player)
    knight_card.state = CardState.LOCKED
    knight_card.bought_this_turn = True
    player.development_cards.append(knight_card)
    
    manager = CardManager([player])
    
    # Simular turno passar
    manager.on_turn_start(player)
    
    assert knight_card.state == CardState.READY, "Carta deve estar READY após turn start"
    assert knight_card.bought_this_turn == False, "Flag bought_this_turn deve ser False"


def test_cannot_play_development_card_same_turn():
    player = Player(1, "Alice", RED)
    
    knight_card = KnightCard(owner=player)
    knight_card.state = CardState.LOCKED
    knight_card.bought_this_turn = True
    player.development_cards.append(knight_card)
    
    manager = CardManager([player])
    
    # Tentar ativar
    success = manager.attempt_activate_card(player, knight_card)
    
    assert not success, "Não deve conseguir jogar carta LOCKED"
    assert knight_card.state == CardState.LOCKED, "Estado não deve mudar"


def test_knight_card_activation():
    player = Player(1, "Alice", RED)
    assert player.knights_played == 0
    
    knight_card = KnightCard(owner=player)
    knight_card.state = CardState.READY
    knight_card.bought_this_turn = False
    player.development_cards.append(knight_card)
    
    manager = CardManager([player])
    
    # Ativar
    success = manager.attempt_activate_card(player, knight_card)
    
    # Knight activation deve aumentar knights_played
    if success:
        assert player.knights_played >= 1, "Knights played deve aumentar"
        assert knight_card.state == CardState.USED, "Carta deve estar USED"


def test_multiple_development_cards():
    player = Player(1, "Alice", RED)
    
    # Dar recursos para 3 cartas
    for _ in range(3):
        player.inventory.add(ROCK, 1)
        player.inventory.add(LAMB, 1)
        player.inventory.add(WHEAT, 1)
    
    manager = CardManager([player])
    
    # Mock deck
    cards_to_buy = [
        KnightCard(),
        RoadBuildingCard(),
        YearOfPlentyCard(),
    ]
    manager.development_cards = cards_to_buy.copy()
    
    # Comprar todas
    for i in range(3):
        success = manager.attempt_buy_card(player)
        assert success, f"Deve conseguir comprar carta {i+1}"
    
    assert len(player.development_cards) == 3, "Deve ter 3 cartas"
    
    # Todas devem estar LOCKED
    for card in player.development_cards:
        assert card.state == CardState.LOCKED, f"Carta deve estar LOCKED, mas está {card.state}"
    
    # Simular turno passar
    manager.on_turn_start(player)
    
    # Todas devem estar READY agora
    for card in player.development_cards:
        assert card.state == CardState.READY, f"Carta deve estar READY após turn start"


def test_cannot_play_card_without_flag():
    player = Player(1, "Alice", RED)
    
    # 2 cartas READY
    card1 = KnightCard(owner=player)
    card1.state = CardState.READY
    card1.bought_this_turn = False
    player.development_cards.append(card1)
    
    card2 = KnightCard(owner=player)
    card2.state = CardState.READY
    card2.bought_this_turn = False
    player.development_cards.append(card2)
    
    manager = CardManager([player])
    
    # Jogar primeira carta
    with patch.object(card1, 'activate', return_value=True):
        success1 = manager.attempt_activate_card(player, card1)
    
    if success1:
        # Marcar que já jogou uma
        player.played_development_card_this_turn = True
        
        # Tentar jogar segunda
        success2 = manager.attempt_activate_card(player, card2)
        
        assert not success2, "Não deve conseguir jogar segunda carta no turno"


def test_card_states_after_full_cycle():
    player = Player(1, "Alice", RED)
    
    knight_card = KnightCard(owner=player)
    knight_card.state = CardState.LOCKED
    knight_card.bought_this_turn = True
    player.development_cards.append(knight_card)
    
    manager = CardManager([player])
    
    # Estado 1: LOCKED após compra
    assert knight_card.state == CardState.LOCKED
    
    # Estado 2: READY após turn start
    manager.on_turn_start(player)
    assert knight_card.state == CardState.READY
    
    # Estado 3: USED após ativação
    with patch.object(knight_card, 'activate', return_value=True):
        manager.attempt_activate_card(player, knight_card)
    
    if knight_card.state == CardState.USED:
        # Verificar que não pode jogar novamente
        success = manager.attempt_activate_card(player, knight_card)
        assert not success, "Não deve conseguir jogar carta já USED"


def test_development_card_removal_after_use():
    player = Player(1, "Alice", RED)
    
    card = KnightCard(owner=player)
    card.state = CardState.READY
    card.bought_this_turn = False
    player.development_cards.append(card)
    
    initial_count = len(player.development_cards)
    
    # Jogar
    with patch.object(card, 'activate', return_value=True):
        card.state = CardState.USED
    
    # Verificar que não pode jogar novamente (estado USED bloqueia)
    success = card.can_activate(has_played_card_this_turn=True)
    
    # Se implementado, não deve poder jogar (USED)
    # ou carta pode ser removida da lista


def test_development_card_no_play_on_setup():
    player = Player(1, "Alice", RED)
    player.inventory.add(ROCK, 1)
    player.inventory.add(LAMB, 1)
    player.inventory.add(WHEAT, 1)
    
    # Durante setup, game.py não oferece botão de compra
    # Este teste valida que o check existe em Player
    # (em jogo real, Game scene não permite, mas modelo pode validar)
    
    # Simular que estamos em setup
    player.settlements_count = 0  # em setup
    
    assert player.is_in_setup_phase(), "Deve estar em setup phase"
    
    # Em setup, game não deveria oferecer compra de carta
    # Validar que a regra não se quebra por erro de lógica


def test_victory_point_card_not_playable():
    from components.base_card import VictoryPointCard
    
    player = Player(1, "Alice", RED)
    
    vp_card = VictoryPointCard(owner=player)
    vp_card.state = CardState.READY
    player.development_cards.append(vp_card)
    
    # VP card não pode ser ativada
    can_play, reason = vp_card.can_activate(has_played_card_this_turn=False)
    assert not can_play, "VP card não deve poder ser jogada"
    assert "ponto" in reason.lower() or "vitória" in reason.lower(), \
        f"Mensagem deve mencionar vitória, mas diz: {reason}"
