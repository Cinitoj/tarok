# AGENT
#	programi za agenta (terminologija RL) *

import random
import json
import math
import itertools
import pickle
from Environment import CARDS, BIDS_VAL, playable_cards, dropable_cards

# kode kart po barvah - uporabno za kodiranje stanj in akcij
CARDS_BY_COLOR = {	'k': {	'4': '0', '3': '1', '2': '2', '1': '3', 'P': '4', 'C': '5', 'Q': '6', 'K': '7'	},
					's': {	'4': '0', '3': '1', '2': '2', '1': '3', 'P': '4', 'C': '5', 'Q': '6', 'K': '7'	},
					'+': {	'7': '0', '8': '1', '9': '2', '10': '3', 'P': '4', 'C': '5', 'Q': '6', 'K': '7'	},
					'p': {	'7': '0', '8': '1', '9': '2', '10': '3', 'P': '4', 'C': '5', 'Q': '6', 'K': '7'	},
					't': {	'I': 'a', 'II': 'b', 'III': 'c', 'IIII': 'd', 'V': 'e', 'VI': 'f', 'VII': 'g', 'VIII': 'h', 'IX': 'i', 'X': 'j', 'XI': 'k', 
							'XII': 'l', 'XIII': 'm', 'XIV': 'n', 'XV': 'o', 'XVI': 'p', 'XVII': 'r', 'XVIII': 's', 'XIX': 't', 'XX': 'u', 'XXI': 'v', 'S': 'z'}	}


# splošne funkcije

# returns the argmax (key) and max (value) from a dictionary
def max_dict(d):
  max_key = None
  max_val = float('-inf')
  for k, v in d.items():
    if v > max_val:
      max_val = v
      max_key = k
  return max_key, max_val

# agent, ki se ne uči in reagira na okolje naključno
class Agent_0 (object):
	def __init__(self, position=0):
		self.position = position												# pozicija agenta v igri
		return

	def reset(self, position=0):
		return

	def make_a_bid(self, bid_candidates):
		bid = random.choice(bid_candidates)
		return bid

	def call_a_king(self, contract):
		king = random.choice(['kK', 'sK', '+K', 'pK'])
		return king

	def switch(self, talon_set, hand):
		cards_taken = random.choice(talon_set)
		drop_candidates = dropable_cards(hand + cards_taken)
		cards_dropped = []
		while len(cards_dropped) < len(cards_taken):
			if len(drop_candidates) == 0:
				drop_candidates = [c for c in hand if (c[0]=='t') and (c not in ['tI', 'tXXI', 'tS'])]
			card = random.choice(drop_candidates)
			cards_dropped.append(card)
			drop_candidates.remove(card)
		return cards_taken, cards_dropped

	def play(self, hand, trick, contract, first_card_idx):
		card = random.choice(playable_cards(hand, trick, contract, first_card_idx, self.position))
		return card

	def get_message(self, info, message1, message2='', message3=''):
		return


# agent, ki ga upravlja človek
class Agent_H (Agent_0):
	def __init__(self, position=0):
		Agent_0.__init__(self, position)
		return

	def reset(self, position=0):
		return

	def get_environment_data(talon, cards_taken, cards_dropped, hand, king, declarer):
		return

	def make_a_bid(self, bid_candidates):
		bid = 'xx'
		while not(bid in bid_candidates):
			bid = input("Koliko igraš? (" + str(bid_candidates) + "): ")
		return bid

	def call_a_king(self, contract):
		king = random.choice(['kK', 'sK', '+K', 'pK'])
		print("Naključno sem klical kralja", king)
		return king

	def switch(self, talon_set, hand):
		x = '-1'
		while int(x) not in range(len(talon_set)):
			print("\nTalon:", talon_set)
			input_str = "Vzemi iz talona (0.." + str(len(talon_set)-1) + "): "
			x = input(input_str)
		cards_taken = talon_set[int(x)]

		drop_candidates = dropable_cards(hand + cards_taken)
		cards_dropped = []
		while len(cards_dropped) < len(cards_taken):
			if len(drop_candidates) == 0:
				drop_candidates = [c for c in hand if (c[0]=='t') and (c not in ['tI', 'tXXI', 'tS'])]

			x = 'xx'
			while x not in drop_candidates:
				print("\nKarte v roki:", [e for e in hand if not (e in cards_dropped)] + [e for e in cards_taken if not (e in cards_dropped)])
				x = input("Založi karto: ")

			cards_dropped.append(x)
			drop_candidates.remove(x)
		return cards_taken, cards_dropped

	def play(self, hand, trick, contract, first_card_idx):
		play_candidates = playable_cards(hand, trick, contract, first_card_idx, self.position)
		print()
		print(" ", hand)

		card ='xx'
		while not(card in play_candidates):
			card = input("  " + str(trick) + '  Izberi karto: ')
		return card

	def get_message(self, info, message1, message2='', message3=''):
		if info == 'hand':
			print("  Karte v roki:", message1)
		return

# agent, ki se uči na podlagi SARSA pristopa
# ideja je, da se vzporedno dogaja pet iger, ki pa so med seboj prepletene. zato pet možnih stanj v vsakem trenutku - odvisno, v kateri barvi se je štih začel
class Agent_AI(Agent_0):
	# inicializira agenta. nekatere vrednosti agenta se zares postavijo na začetno vrednost šele z resetom. te spremenljivke so tukaj zapisane zaradi pregleda nad celoto
	def __init__(self, position=0, n_players=4, ALPHA=0.1, GAMMA=0.9, explain=[], exploit=False):
		Agent_0.__init__(self, position)
		
		self.n_players = n_players
		self.explain = explain 							# razlaga svoje poteze, če je aktivnost v seznamu ['Bid', 'Switch', 'Play', 'Learn'] ali ne, če je zenam prazen
		self.exploit = exploit 							# če False, potem maksimizira exploit fazo na račun explore
		self.observation = 	{	'hand': [], 'talon': [], 'cards_taken': [], 'cards_dropped': [], 'declarer': -1, 'contract': -1, 'king': 'xX',
								'fallen': [], 'score': []	}
		self.deduction =	{	'teams': [], 'home_team': [], 'no_color': []	}
		
		self.ALPHA = ALPHA 								# alpha parameter pri SARSA učenju - learning rate
		self.GAMMA = GAMMA 								# gamma parameter pri SARSA učenju - discount factor
		self.Q = {}										# slovar za "action value" funkcijo
		self.sar = []									# buffer za state-action-reward podatke
		self.last_s = ''								# zadnje uporabljeno stanje
		self.last_a = ''								# zadnja uporabljena akcija

		self.sum_change = 0								# pri vsaki igri seštevam vse spremembe (da lahko kasneje izračunam povprečno spremembo)
		self.dic_difference = {}						# ocena razdalje med dvema kartama

		print("Agent_AI", position, "n = ", n_players, "alpha = ", ALPHA, "gamma = ", GAMMA, "explain = ", explain, "exploit = ", exploit)
		return

	# naloži "action-value" tabelo Q. tip datoteke za shranjevanje ugotovi iz končnice imena datoteke: 'jsn' - json, 'pck' - pickle
	def load(self, file_name):
		save_type = file_name[-3:]
		try:
			if save_type == 'jsn':
				with open(file_name, 'r') as file:
					json_list = json.load(file)
					self.Q = json_list[0]
			else:
				with open(file_name, 'rb') as file:
					self.Q = pickle.load(file)
					for i in range(9):
						q_i = pickle.load(file)
						self.Q.update(q_i)
		except FileNotFoundError:
			print(file_name, "not loaded/doesn't exist")
		except:
			print("Hm, something has gone wrong with loading...", file_name)
		else:
			print("Agent_AI", self.position, "loaded from", file_name, "(" +str(len(self.Q)) + ")")

		print("Agent_AI", self.position,"loading dic_difference...", end='')
		with open('distance.txt', 'r') as file:
			json_list = json.load(file)
			self.dic_difference = json_list
			print("loaded")
		return

	# shrani "action-value" tabelo Q. tip datoteke za shranjevanje ugotovi iz končnice imena datoteke: 'jsn' - json, 'pck' - pickle
	def save(self, file_name):
		print("Agent_AI", self.position,"saving to", file_name, "(" +str(len(self.Q)) + ")", "...", end='')
		save_type = file_name[-3:]
		if save_type == 'jsn':
			json_text = json.dumps([self.Q], indent=4)
			with open(file_name, 'w') as file:
			    file.write(json_text)
		else:
			split_idx = len(self.Q) // 10								# delim na več delov zaradi težav s pomnilnikom
			with open(file_name, 'wb') as file:
				for i in range(9):
					q_i = dict(list(self.Q.items())[split_idx*i:split_idx*(i+1)])
					pickle.dump(q_i, file, pickle.HIGHEST_PROTOCOL)
				q_i = dict(list(self.Q.items())[split_idx*9:])
				pickle.dump(q_i, file, pickle.HIGHEST_PROTOCOL)
		print(" saved.")
		return

	# nastavi začetne vrednosti agenta
	def reset(self, n_players, position=0):
		self.n_players = n_players
		self.observation = 	{	'hand': [], 'talon': [], 'cards_taken': [], 'cards_dropped': [], 'declarer': -1, 'contract': -1, 'king': 'xX',
								'fallen': [], 'score': []}
		self.deduction =	{	'teams': ['team_x'] * self.n_players, 'home_team': [], 'no_color': [[]] * self.n_players }
		self.sar = []
		return

	# zakodira stanje kart v state. to kodiranje je zanimivo za avkcije in menjavo kart
	def state1(self, hand):
		def state_col(color):
			code = ''
			for c in [color+'K', color+'Q']:
				if c in hand:
					code += '1'
				else:
					code += '0'
			n = len([e for e in ['4', '3', '2', '1', '7', '8', '9', '10', 'P', 'C'] if color+e in hand])
			return str(int(code,2)) + str(n)

		def state_tar():
			code = ''
			for c in ['tI', 'tXXI', 'tS']:
				if c in hand:
					code += '1'
				else:
					code += '0'
			n_ii_xv = str(len([e for e in CARDS[33:47] if e in hand]))
			n_xvi_xx = str(len([e for e in CARDS[47:52] if e in hand]))
			return str(int(code,2)) + '{:>2}'.format(n_ii_xv) + '{:>2}'.format(n_xvi_xx)

		s = []
		for color in ['k', 's', '+', 'p']:
			s.append(state_col(color))
		s.sort()
		s.append(state_tar())
		s = ''.join(s)
		#print("263 ("+s+")  ", hand)
		return s

	# poišče najbližje stanje začetnemu stanju roke, ki že ima vrednost v Q(s) in za katerega obstaja akcija a
	def closest_state(self, s, a):
		n = len(s)
		s0 = s
		min_distance = 100
		for s1 in self.Q:
			if (s1[2] == '-') and (self.Q[s1] != {}):
				distance = 0
				for i in range(n):
					if (s1[i] != '-') and (s1[i] != ' ') and (s[i] != ' '):
						#print("276", s1, s, i)
						distance += abs(int(s1[i]) - int(s[i]))
				if (min_distance > distance) and (a in self.Q[s1]):
					min_distance = distance
					s0 = s1
				# print("274", s, s1, distance)
				if min_distance <3:
					break
		# print("280", s, s0, min_distance)
		return s0

	# izbere največji element v Q listi. Če elementov več, potem izbere naključno med njimi. vrne indeks največjega elementa
	def max_q(self, q_candidates):
		mx = max(q_candidates)
		first_time_candidates = []
		for idx in range(len(q_candidates)):
			if q_candidates[idx] == mx:
				first_time_candidates.append(idx)

		if first_time_candidates != []:
			card_idx = random.choice(first_time_candidates)
		else:
			card_idx = q_candidates.index(max(q_candidates))
		return card_idx

	# licitira - izbira med možnimi licitacijami. ker je pass vedno zadnja možnost, je vedno vključena
	def make_a_bid(self, bid_candidates):
		s = self.state1(self.observation['hand'])
		q_candidates = []
		a_candidates = []

		s0 = s
		for a in bid_candidates:
			if self.exploit:
				if s in self.Q:
					if a in self.Q[s]:
						s0 = s
					else:
						s0 = self.closest_state(s, a)						# če ne obstaja Q(s,a), potem poišče tak najbližji s0, da obstaja Q(s0,a)
				else:
					s0 = self.closest_state(s, a)							# če ne obstaja Q(s), potem poišče tak najbližji s0, da obstaja Q(s0,a)

			a_candidates.append(a)

			if not (s0 in self.Q):
				self.Q[s0] = {}
				q_candidates.append(125)
			elif not (a in self.Q[s0]):
				q_candidates.append(125)
			else:
				q_candidates.append(self.Q[s0][a])

		idx = self.max_q(q_candidates)
		a = a_candidates[idx]
		self.last_s = s0
		self.last_a = a

		self.explanation('Bid', bid_candidates, q_candidates, self.observation['hand'], a)
		return a

	# preišče vse možnosti prehodov v novo stanje in se odloči za najboljšo
	def switch(self, talon_set, hand):
		n = len(talon_set[0])
		q_candidates = []
		taken_candidate_list = []
		drop_candidate_list = []
		state_list = []
		mandatory_drop = []										# ta množica se napolni, kadar je potrebno založiti nekaj tarokov (vsebuje obvezne netaroke za založit)
		for t_c in talon_set:
			drop_candidates = dropable_cards(hand + t_c)

			if len(drop_candidates) < n:						# ko je potrbno založiti taroke
				mandatory_drop = drop_candidates
				drop_candidates = [c for c in hand if (c[0] == 't') and not (c in ['tI', 'tXXI', 'tS'])]
				n = n - len(mandatory_drop)

			drop_candidates = itertools.combinations(drop_candidates, n)

			for d_c in drop_candidates:
				hand2 = [e for e in hand + t_c if not (e in d_c or e in mandatory_drop)]
				s = self.state1(hand2)

				if s in self.Q:
					if 'e' in self.Q[s]:
						q_candidates.append(self.Q[s]['e'])
					elif 'pass' in self.Q[s]:
						q_candidates.append(self.Q[s]['pass'])
					else:				
						q_candidates.append(125)
				else:
					self.Q[s] = {}
					if self.exploit:
						s0 = self.closest_state(s, 'e')
						if 'e' in self.Q[s0]:
							q_candidates.append(self.Q[s0]['e'])
						else:
							q_candidates.append(125)
					else:
						q_candidates.append(125)
				
				state_list.append(s)
				taken_candidate_list.append(t_c)
				drop_candidate_list.append(list(d_c) + mandatory_drop)

		idx = self.max_q(q_candidates)
		s = state_list[idx]
		cards_taken = taken_candidate_list[idx]
		cards_dropped = drop_candidate_list[idx]
		self.last_s = s
		self.last_a = 'e'

		self.explanation('Switch', zip(taken_candidate_list, drop_candidate_list), q_candidates, cards_taken, cards_dropped)
		return cards_taken, cards_dropped

	# razloži svojo odločitev, če je aktivnost v seznamu za razlage self.explain. možnosti so ['Bid', 'Switch', 'Play', 'Learn']
	def explanation(self, activity, candidates, q_candidates, start_state, result):
		if activity in self.explain:
			print("    Player", self.position, "Activity", activity, start_state, "->", result, "  ", self.last_s, self.last_a)
			for c, q in zip(candidates, q_candidates):
				print("      ", c, q)
		return

	# sprejme sporočilo od game objekta in izvede ustrezno akcijo (zapiše podatek, se uči,...)
	def get_message(self, info, message1, message2='', message3=''):
		if (info == 'cards_dropped') or (info == 'trick'):
			self.observation['fallen'] += message1
			self.observation['hand'] = [e for e in self.observation['hand'] if not(e in message1)]
			self.observation[info] = message1
		elif info == 'cards_taken':
			self.observation['fallen'] += [e for e in self.observation['talon'] if not (e in message1)]
			self.observation[info] = message1
			if self.observation['declarer'] == self.position:
				self.observation['hand'] = self.observation['hand'] + message1
		else:
			self.observation[info] = message1

		if info == 'contract':
			self.sar.append((self.last_s, self.last_a, 0.))
			if self.observation['contract'] == 'klop':										# če se igra klop, vsak igra sam za sebe
				self.deduction['teams'] = ['team_A', 'team_B', 'team_C', 'team_D']
				self.deduction['teams'] = self.deduction['teams'][:self.n_players]
			else:																			# sicer je declarer sam, ostali so skupaj
				self.deduction['teams'] = ['team_B'] * self.n_players
				self.deduction['teams'] = self.deduction['teams'][:self.n_players]
				self.deduction['teams'][self.observation['declarer']] = 'team_A'

		if info == 'cards_dropped':
			self.sar.append((self.last_s, self.last_a, 0.))

		if info == 'king':																	# kadar se kliče kralj, se timi spremenijo
			if self.observation['king'] in self.observation['hand']:						# če držim kralja jaz, se priključim timu declarerja
				self.deduction['teams'][self.position] = 'team_A'

		if (info == 'trick') and (self.n_players == 4) and (self.observation['king'] in message1):			# določanje timov med igro
			self.deduction['teams'] = ['team_B'] * self.n_players
			self.deduction['teams'][self.observation['declarer']] = 'team_A'
			self.deduction['teams'][message1.index(self.observation['king'])] = 'team_A'

		self.deduction['home_team'] = [i for i, value in enumerate(self.deduction['teams']) if value == self.deduction['teams'][self.position]]

		if info == 'trick':
			# preverjanje škrtosti
			for c in message1:
				if c[0] != message1[message2[0]][0]:
					c_idx = message1.index(c)
					if c_idx < self.n_players:											# preprečitev situacij, ki jih povzroči klop s priboljški
						self.deduction['no_color'][c_idx].append(message1[message2[0]][0])
						if (c[0] != 't') and (message1[message2[0]][0] != 't'):
							self.deduction['no_color'][c_idx].append('t')

			# učenje SARSA - zapisovanje podatkov epizode
			r = 0
			if message2[1] in self.deduction['home_team']:
				r = message2[2]

			if self.observation['contract'] != 'klop':
				# če izgubi XXI, to takoj upošteva pri učenju (rewardu odšeteje 21)
				if (message1[self.position] == 'tXXI') and (message2[1] != self.position):	
					r -= 21

				# preveri, če se je delal pagat ultimo in to upošteva pri učenju
				if self.observation['hand'] == []:						# če je zadnji štih in...
					if message1[self.position] == 'tI':					# sem vrgel pagata in...
						if message2[1] == self.position:				# sem naredil pagata ultimo
							r += 25										# se pri rewardu prišteje 25 točk
						else:
							r -= 25										# če pa nisem dobil, se odštejejo
			self.sar.append((self.last_s, self.last_a, r))


		# # učenje SARSA - začne se ob zaključku epizode
		# if info == 'score':
		# 	self.sum_change = 0
		# 	(s, a, r) = self.sar.pop()
		# 	if not(a in self.Q[s]):
		# 		self.Q[s][a] = 125
		# 	old_qsa = self.Q[s][a]
		# 	self.Q[s][a] = old_qsa + self.ALPHA*(r - old_qsa)		# izračun Q(s,a) za končno stanje

		# 	if 'Learn' in self.explain:
		# 		print("    ", self.Q[s][a], "=", old_qsa, "+ alpha*(", r, "-", old_qsa, ")", end="")
		# 		print("    s=", s, "a=", a)

		# 	while self.sar != []:									# izračun Q(s,a) za ostala stanja (od zadnjega proti prvemu)
		# 		a2 = a 												# s2,a2 - naslednje stanje
		# 		s2 = s
		# 		(s, a, r) = self.sar.pop()

		# 		if a in ['3', '2', '1']:							# če je akcija klicanje igre, potem je reward točkovanje igre (+ za  zmago, - za poraz)
		# 			if message2[self.position] > 35:
		# 				r = BIDS_VAL[a]
		# 			else:
		# 				r = -BIDS_VAL[a]
				
		# 		if (a == 'pass') and (self.observation['contract'] == 'klop'):
		# 			if self.position in message1['klop0']:
		# 				r = 70
		# 			elif self.position in message1['klop70']:
		# 				r = -70

		# 		if a == 'e':
		# 			if message1['valat'] != []:
		# 				if self.position in message1['valat']:
		# 					r = 250
		# 				else:
		# 					r = -250
		# 			if message1['king4'] != []:
		# 				if self.position in message1['king4']:
		# 					r += 10
		# 				else:
		# 					r -= 10
		# 			if message1['trula3'] != []:
		# 				if self.position in message1['trula3']:
		# 					r += 10
		# 				else:
		# 					r -= 10

		# 		if not(a in self.Q[s]):
		# 			old_qsa = 125
		# 			self.Q[s][a] = round(125 + 0.5*(r + self.Q[s2][a2] - 125), 3)
		# 		else:
		# 			old_qsa = self.Q[s][a]
		# 			self.Q[s][a] = round(old_qsa + self.ALPHA*(r + self.GAMMA*self.Q[s2][a2] - old_qsa), 3)
		# 			self.sum_change += abs(self.Q[s][a] - old_qsa)

		# 		if 'Learn' in self.explain:
		# 			print("    ", self.Q[s][a], "=", old_qsa, "+ alpha*(", r, "+ gamma*", self.Q[s2][a2], "-", old_qsa, ")", end="")
		# 			print("    s=", s, "a=", a, "s2=", s2, "a2=", a2)



		# učenje SARSA - začne se ob zaključku epizode !!!!!
		if info == 'score':
			self.sum_change = 0

			# zadnji štih. največja možnost za reward je štiri karte po pet točk + pagat in kralj ultimo => 60
			(s, a, r) = self.sar.pop()
			if not(a in self.Q[s]):
				old_qsa = 60
				self.Q[s][a] = round(old_qsa + 0.8*(r - old_qsa), 3)
			else:
				old_qsa = self.Q[s][a]
				self.Q[s][a] = round(old_qsa + self.ALPHA*(r - old_qsa), 3)		# izračun Q(s,a) za končno stanje
			self.sum_change += abs(self.Q[s][a] - old_qsa)

			if 'Learn' in self.explain:
				print("    ", self.Q[s][a], "=", old_qsa, "+ alpha*(", r, "-", old_qsa, ")", end="")
				print("    s=", s, "a=", a)

			# izračun Q(s,a) za ostala stanja (od zadnjega proti prvemu)
			while self.sar != []:									
				a2 = a 												# s2,a2 - naslednje stanje
				s2 = s
				(s, a, r) = self.sar.pop()

				# izračun Q(s,a) za poteze v igri max = 70 točk + ultimo kralj in pagat = 105
				if not (a in ['3', '2', '1', 'pass', 'e']):
					if not(a in self.Q[s]):
						old_qsa = 105
						self.Q[s][a] = round(old_qsa + 0.8*(r + self.GAMMA*self.Q[s2][a2] - old_qsa), 3)
					else:
						old_qsa = self.Q[s][a]
						self.Q[s][a] = round(old_qsa + self.ALPHA*(r + self.GAMMA*self.Q[s2][a2] - old_qsa), 3)
					self.sum_change += abs(self.Q[s][a] - old_qsa)

					if 'Learn' in self.explain:
						print("    ", self.Q[s][a], "=", old_qsa, "+ alpha*(", r, "+ gamma*", self.Q[s2][a2], "-", old_qsa, ")", end="")
						print("    s=", s, "a=", a, "s2=", s2, "a2=", a2)

				else:
					# izračun Q(s,a) za avkcijo in licitacijo
					r = message3[self.position]

					if (a in ['pass', 'e']):
						Qs2a2 = 0
					else:
						Qs2a2 = self.Q[s2][a2]

					if not(a in self.Q[s]):
						old_qsa = 160
						self.Q[s][a] = round(old_qsa + 0.8*(r + self.GAMMA*Qs2a2 - old_qsa), 3)
					else:
						old_qsa = self.Q[s][a]
						self.Q[s][a] = round(old_qsa + self.ALPHA*(r + self.GAMMA*Qs2a2 - old_qsa), 3)
					self.sum_change += abs(self.Q[s][a] - old_qsa)

					if 'Learn' in self.explain:
						print("    ", self.Q[s][a], "=", old_qsa, "+ alpha*(", r, "+ gamma*", Qs2a2, "-", old_qsa, ")", end="")
						print("    s=", s, "a=", a, "s2=", s2, "a2=", a2)
		return

	# zakodira stanje igre
	def state(self, color):
		def state_color(cards_of_interest, color):
			code_col = ''
			for c in cards_of_interest:
				if (color + c) in self.observation['hand']:
					code_col += '1'
				elif (color + c) in self.observation['fallen']:
					code_col += '2'
				else:
					code_col += '0'
			return str(int(code_col, 3))

		def state_tarok(cards_of_interest):
			code_tar = ''
			tar_hand = len([e for e in cards_of_interest if e in self.observation['hand']])
			tar_fall = len([e for e in cards_of_interest if e in self.observation['fallen']])
			code_tar = str(min(tar_hand, 6)) + '/' + str(min(22 - tar_hand - tar_fall, 6))
			return code_tar
			
		state_code = str(int(self.observation['contract'] == 'klop')) + ':'
		if color != 't':
			state_code += state_color(CARDS_BY_COLOR[color], color) + ':' + state_tarok(CARDS[32:])    # + ':' + state_teams()
			if self.n_players == 4:
				state_code += ':' + str(int(self.observation['king'][0] == color))
		else:
			state_code += state_color(['I', 'XVIII', 'XIX', 'XX', 'XXI', 'S'], 't') + ':' + state_tarok(CARDS[33:49])
		return state_code

	# zakodira akcijo. štih obrne tako, da je prva karta v štihu tista, ki je prva padla
	def action(self, trick, first_card_idx):
		CARD_TO_CHR = { 	'k4': 'a', 'k3': 'b', 'k2': 'c', 'k1': 'd', 'kP': 'e', 'kC': 'f', 'kQ': 'g', 'kK': 'h',
					's4': 'i', 's3': 'j', 's2': 'k', 's1': 'l', 'sP': 'm', 'sC': 'n', 'sQ': 'o', 'sK': 'p',
					'+7': 'q', '+8': 'r', '+9': 's', '+10': 't', '+P': 'u', '+C': 'v', '+Q': 'w', '+K': 'z',
					'p7': '0', 'p8': '1', 'p9': '2', 'p10': '3', 'pP': '4', 'pC': '5', 'pQ': '6', 'pK': '7', 
					'tI': 'A', 'tII': 'B', 'tIII': 'C', 'tIIII': 'D', 'tV': 'E', 'tVI': 'F', 'tVII': 'G', 'tVIII': 'H', 'tIX': 'I', 'tX': 'J', 
					'tXI': 'K', 'tXII': 'L', 'tXIII': 'M', 'tXIV': 'N', 'tXV': 'O', 'tXVI': 'P', 'tXVII': 'Q', 'tXVIII': 'R', 'tXIX': 'S', 'tXX': 'T', 
					'tXXI': 'U', 'tS': 'V',
					'!!': '!', '!x': '%', 'x!': '&', 'xx': '#', '--': '-', '-X': ':', 'X-': '.', 'XX': '*'}  # partner (nn, nd,dn, dd) nepartner (nn, nd,dn, dd)

		def ac(no_col, partner):
			if no_col:
				if partner:
					ch = '!'
				else:
					ch = '-'
			else:
				if partner:
					ch = 'x'
				else:
					ch = 'X'
			return ch

		action_code = ''
		for i in range(self.n_players):
			j = (i + first_card_idx) % self.n_players										# premesti karte v štihu, tako da si sledijo od 0 naprej
			if trick[j] == '--':															# če karta še ni padla, jo zakodira z znanjem o škrtosti
				partner = self.deduction['teams'][self.position] == self.deduction['teams'][j]

				card1 = ac(trick[first_card_idx][0] in self.deduction['no_color'][j], partner)
				card1 += ac('t' in self.deduction['no_color'][j], partner)

				action_code += CARD_TO_CHR[card1]
			else:
				action_code += CARD_TO_CHR[trick[j]]

		return action_code

	# poišče približek vrednosti Q(s,a) tako, da karto c zamenja z najbližjo c2, sicer vrne 125
	def Q_approx(self, c, trick, first_card_idx):
		approx_candidates = [e + c for e in CARDS] + [c + e for e in CARDS]
		approx_candidates = [e for e in approx_candidates if e in self.dic_difference ]			# seznam gesel, kjer bom iskal nadomestno oceno
		c2 = 'xx'
		min_e = 10000
		for e in approx_candidates:
			if min_e > self.dic_difference[e]:
				min_e = self.dic_difference[e]
				if e[:len(c)] == c:			# c je v prvem delu para kart
					c2 = e[len(c):]
				else:
					c2 = e[:-len(c)]

		if not (c2 in self.observation['hand']) and (c2 != 'xx') and not (c2 in trick):
			self.observation['hand'].append(c2)													# prirediš karte v roki
			self.observation['hand'].remove(c)

			s2 = self.state(c2[0])
			trick2 = [e for e in trick]
			trick2[self.position] = c2
			a2 = self.action(trick2, first_card_idx)

			q = 125
			if s2 in self.Q:
				if a2 in self.Q[s2]:
					q = self.Q[s2][a2]

			self.observation['hand'].remove(c2)													# restavriraš pravo stanje
			self.observation['hand'].append(c)
		else:
			q = 125
		return q

	# glede na stanje v roki in znanje izbere najboljšo karto za štihu 	
	def play(self, hand, trick, contract, first_card_idx):
		play_candidates = playable_cards(hand, trick, contract, first_card_idx, self.position)
		if len(hand) != len(self.observation['hand']):
			print("581", hand, self.observation['hand'])
			x = input("opa")
		trick_candidates = []									# preišče vse kandidate za akcijo in če ne obstaja Q[s][a], ga zapiše z vrednostjo 125
		q_candidates = []										# ustrezne vrednosti Q za vsak trick v trick_candidates
		s_candidates = []
		a_candidates = []
		for c in play_candidates:
			s = self.state(c[0])								# state se sestavi glede na karto, ki jo mečem
			if not (s) in self.Q:
				self.Q[s] = {}

			trick2 = [e for e in trick]
			trick2[self.position] = c
			a = self.action(trick2, first_card_idx)

			if a in self.Q[s]:
				q_candidates.append(self.Q[s][a])
			elif self.exploit:
				q_candidates.append(self.Q_approx(c, trick, first_card_idx,))					# poišče najboljši približek
			else:
				q_candidates.append(125)

			trick_candidates.append(trick2)
			s_candidates.append(s)
			a_candidates.append(a)

		card_idx = self.max_q(q_candidates)
		card = play_candidates[card_idx]
		self.last_s = s_candidates[card_idx]
		self.last_a = a_candidates[card_idx]

		self.explanation('Play', play_candidates, q_candidates, trick, card)
		return card


