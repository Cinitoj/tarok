# Play
# pripravljen za igranje Taroka

import random
import json
from Agent import Agent_0, Agent_H, Agent_AI
from Environment import Tarok

print('------------------------------------------------------------------------------------------------- START ------------------------------------')

# igralci, ki so na voljo
A = Agent_AI(ALPHA=0.1, GAMMA=0.9, explain=[], exploit=False)
B = Agent_AI(ALPHA=0.1, GAMMA=0.9, exploit=False)
C = Agent_AI(ALPHA=0.1, GAMMA=0.9)
X = Agent_0()
Y = Agent_0()
Z = Agent_0()
H = Agent_H()

game = Tarok([H, A, B, None], verbose='Basic')

A.load('Qv.pck')
# B.load('Q3.jsn')
# C.load('Q3.jsn')
B.Q = A.Q 				# kazalec Q finkcije agenta B kaže na Q funkcijo agenta A: v bistvu poteze črpata iz istega znanja

looser = ['Auč! A boli?', 'Sej bo drugič bolje!', 'Sem pa več pričakoval od tebe!', 'A ti danes ne gre?', "A boš jokcala?", "Pasiansa je bolj igra zate..." ]
looser += ["Mogoče nisi prebrala pravil?", "So izgovori in so rezultati.", "Ni važno, koliko tečeš, ampak koliko golov daš!", "Weee, weee..."]
looser += ["Ti si ena zguba.", "Si se že navadila izgubljati?", "Vesela zguba je skoraj zmagovalec!", "A je to vse, kar znaš????"]
winner = ['Najbolj neumen kmet ima najbolj debel krompir.', 'Kako se ti je pa to usralo?', 'Označene karte, kaj pa drugega!', 'A upaš še eno?', "Začetniška sreča..."]
winner += ["Zmagovanje ni vse.", "Rabim motivacijo, zato ti dajem malo prednosti."]

N = int(input("Koliko iger želiš igrati? "))

score = [0] * game.n_players
for i in range(0, N, 1):
	game.start_player = i % game.n_players
	print("\n\n*****************************************************************************")
	print("Igra št.", i+1, ", obvezno 3 ima igralec", game.start_player, "\n")
	game.episode()
	for k in range(game.n_players):
		score[k] += game.total_score[k]

	if (game.total_score[0] < game.total_score[1]) and (game.total_score[0] < game.total_score[2]):
		print(random.choice(looser))
	elif (game.total_score[0] > game.total_score[1]) and (game.total_score[0] > game.total_score[2]):
		print(random.choice(winner))

	print("\nTrenutni skupni rezultat je", score)

