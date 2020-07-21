# ENVIRONMENT
#	objekt Tarok vsebuje predvsem podatke o igri (environment), ki seveda niso razvidni v celoti posameznemu igralcu.
#	objekt vsebuje tudi preprostejše kalkulacije in metode, ki so pomembne za igro
#	sama mehanika igre se dogaja izven objekta

import random
from boltons import iterutils

# CONSTANTS
# seznam igralnih kart
CARDS = [	'k4', 'k3', 'k2', 'k1', 'kP', 'kC', 'kQ', 'kK',
			's4', 's3', 's2', 's1', 'sP', 'sC', 'sQ', 'sK',
			'+7', '+8', '+9', '+10', '+P', '+C', '+Q', '+K',
			'p7', 'p8', 'p9', 'p10', 'pP', 'pC', 'pQ', 'pK', 
			'tI', 'tII', 'tIII', 'tIIII', 'tV', 'tVI', 'tVII', 'tVIII', 'tIX', 'tX', 'tXI',	'tXII',
			'tXIII', 'tXIV', 'tXV', 'tXVI', 'tXVII', 'tXVIII', 'tXIX', 'tXX', 'tXXI', 'tS' ]

# vrednost posamezne igralne karte
CARD_VAL = { 	'k4': 1, 'k3': 1, 'k2': 1, 'k1': 1, 'kP': 2, 'kC': 3, 'kQ': 4, 'kK': 5,
				's4': 1, 's3': 1, 's2': 1, 's1': 1, 'sP': 2, 'sC': 3, 'sQ': 4, 'sK': 5,
				'+7': 1, '+8': 1, '+9': 1, '+10': 1, '+P': 2, '+C': 3, '+Q': 4, '+K': 5,
				'p7': 1, 'p8': 1, 'p9': 1, 'p10': 1, 'pP': 2, 'pC': 3, 'pQ': 4, 'pK': 5, 
				'tI': 5, 'tII': 1, 'tIII': 1, 'tIIII': 1, 'tV': 1, 'tVI': 1, 'tVII': 1, 'tVIII': 1, 'tIX': 1, 'tX': 1, 'tXI': 1, 'tXII': 1, 
				'tXIII': 1, 'tXIV': 1, 'tXV': 1, 'tXVI': 1, 'tXVII': 1, 'tXVIII': 1, 'tXIX': 1, 'tXX': 1, 'tXXI': 5, 'tS': 5 }

# možne licitacije
BIDS = ['3', '2', '1', 'pass']

# velikost skupin v talonu za menjavo kart
SWITCH_SET = {'3': 3, '2': 2, '1': 1}

# vrednost igre po posamezni licitaciji
BIDS_VAL =	{'klop': 0, '3': 10, '2': 20, '1': 30}


# COMMON PROCEDURES

# Izračuna vrednost seznama ne glede na število kart v njem.
# Matematično štetje kart zgleda takole: od vrednosti vsake karte se odšteje 2/3 točke. Npr. seštevek 3 platercev: 1/3 + 1/3 + 1/3 = 3/3 = 1.
def count_points(pile):
	val_list = [CARD_VAL[e] for e in pile]
	val = sum(val_list) - len(val_list) * 2/3
	return round(val, 1)

# ugotovi zmagovalca štiha
def trick_winner(start_player, trick):
	winning_candidates = [c for c in trick if c[0]=='t']						# preveri, če je padel kakšen tarok	
	if winning_candidates == []:												# če ni taroka, potem odločajo barve v prvi barvi	
		winning_candidates = [c for c in trick if c[0]==trick[start_player][0]]								
		
	winning_candidates.sort(key = CARDS.index, reverse = True)					# sortiraš po velikost 
	winner = trick.index(winning_candidates[0])

	if ('tI' in trick) and ('tXXI' in trick) and ('tS' in trick):
		winner = trick.index('tI')												# "The Emperor trick" - NE VELJA EDINO PRI BARVNEM VALATU
	return winner

# glede na trick izbere iz roke trenutnega igralca karte, s katerimi je dovoljeno igrati. 
def playable_cards(hand, trick, contract, first_card_idx, next_card_idx):
	if trick[first_card_idx] == ('--'):											# če barva še ni izbrana, potem so kandidati vse karte v roki
		candidates = hand.copy()
	else:
		candidates = [c for c in hand if c[0] == trick[first_card_idx][0]]		# poišče vse karte v roki, ki so v barvi prve karte
		if candidates == []:													# če je škrt, poišče vse taroke v roki
			candidates = [c for c in hand if c[0] == 't']
		if candidates == []:													# če nima niti tarokov, potem so kandidati za igro kar vse karte v roki
			candidates = hand.copy()

		if contract in ['klop']:
			trick2 = trick.copy()
			neg_candidates = []
			for c in candidates:
				trick2[next_card_idx] = c
				if trick_winner(first_card_idx, trick2) == next_card_idx:
					neg_candidates.append(c)
			if neg_candidates != []:
				candidates = neg_candidates

	if (contract == 'klop') and ('tI' in candidates) and (len(candidates) > 1):							# tI mora pasti kot zadnja možnost
		candidates.remove('tI')
	return candidates

# glede na igro in roko izbere karte, ki jih je dovoljeno založiti. ne smeš se založiti taroka niti kralja. če ne gre, potem se založiš taroka, vendar ne trule.
def dropable_cards(hand):
	h = [e for e in hand if (e[0] != 't') and (e[1] != 'K')]
	return h


# TAROK
class Tarok (object):

	# inicializacija objekta okolja. večina spremenljivk se ustreno nastavi v reset - tukaj so zapisane zaradi preglednosti
	def __init__(self, players=[None, None, None, None], verbose='None'):
		# Misc
		self.verbose = verbose							# 'None' - ne izpisuje; 'Basic' - izpisuje kar je vidno opazovalcu; 'All' - izpisuje vse
		self.n_players = 4 - players.count(None)		# število igralcev v igri
		self.players = players[:self.n_players] 		# seznam igralcev, vsakemu se dodeli pozicija v igri
		for p in self.players:
			p.position = self.players.index(p)

		# Cards
		self.hands = []									# karte, ki jih drži posamezen igralec v roki: [[]] * n_players
		self.talon = []
		self.trick_pile =[]								# odigrane karte - štihi
		self.trick_pile_meta = []						# meta podatki o štihih. [1, 2, 5] : prvi je vrgel 1, pobral je 2, vrednost štiha je 5

		# Licitation
		self.start_player = 0							# prvi, ki licitira, ima prednost in "obvezno 3". običajno tudi prvi odpre igro
		self.declarer = -1								# zmagovalec licitacije
		self.contract = -1								# igra, ki jo igra zmagovalec licitacije
		self.king = 'xX'								# kralj, ki ga kliče zmagovalec licitacije

		# Switch
		self.cards_taken = []							# karte, ki jih declarer vzame iz talona
		self.cards_dropped = []							# karte, ki jih declarer zamenja za karte iz talon (odloži)
		self.king_from_talon_passed = False				# declarer se je zarufal, dvignil klicanega kralja iz talona in ga spravil okoli

		# Play
		self.teams = []									# imena timov, kjer igra posamezen igralec. 'team_A' je običajno declarer

		# Score
		self.trick_points = [0] * self.n_players		# osvojene točke iz štihov za vsakega igralca
		self.total_score = [0] * self.n_players			# seštevek vseh iger za vsakega posameznika
		self.bonus_dic = {'valat': [], 'klop0': [], 'klop70': [], 'king+': [], 'king-': [], 'tI+': [], 'tI-': [], 'tXXI-': [], 'king4': [], 'trula3': []}
		return

	# resetira parametre okolja za začetek nove igre
	def reset(self):
		self.hands = []
		self.talon = []
		self.trick_pile =[]
		self.trick_pile_meta = []
		self.declarer = -1
		self.contract = -1
		self.king = 'xX'
		self.king_from_talon_passed = False
		self.teams = []
		self.trick_pile =[]
		self.trick_pile_meta = []
		self.trick_points = [0] * self.n_players
		self.total_score = [0] * self.n_players
		for player in self.players:
			player.reset(self.n_players)
		self.bonus_dic = {'valat': [], 'klop0': [], 'klop70': [], 'king+': [], 'king-': [], 'tI+': [], 'tI-': [], 'tXXI-': [], 'king4': [], 'trula3': []}
		return

	# razdeli karte za začetek igre
	def deal_cards(self):
		deck = CARDS.copy()
		for k in range(self.n_players):
			hand = random.sample(deck, 48//self.n_players)
			hand.sort(key = CARDS.index)
			self.hands.append(hand)
			deck = [e for e in deck if e not in hand]
		random.shuffle(deck)
		self.talon = deck
		return

	# licitacija. najprej se preveri obvezni klop.
	# licitiraš lahko samo nad že licitiranimi izbirami, razen če imaš prednost
	def auction(self):
		def has_priority(player1, player2):
			return (player1-self.start_player) % self.n_players < (player2-self.start_player) % self.n_players

		compulsory_klop = False														# obvezno se igra klop, če je kdo brez taroka
		for hand in self.hands:
			compulsory_klop = (len([e for e in hand if e[0]=='t']) == 0) or compulsory_klop

		if not compulsory_klop:
			last_bids = [None] * self.n_players										# zadnja licitirana vrednost vsakega igralca
			last_bids[self.start_player] = '3'										# obvezna tri
			highest_bidder = self.start_player
			current_bidder = self.start_player
			while last_bids.count('pass') != self.n_players - 1:					# dokler ne gredo naprej vsi razen enega...
				current_bidder = (current_bidder + 1) % self.n_players
				if last_bids[current_bidder] != 'pass':
					if has_priority(current_bidder, highest_bidder):
						last_bids[current_bidder] = self.players[current_bidder].make_a_bid(BIDS[BIDS.index(last_bids[highest_bidder]):])
					else:
						last_bids[current_bidder] = self.players[current_bidder].make_a_bid(BIDS[BIDS.index(last_bids[highest_bidder])+1:])

					if last_bids[current_bidder] != 'pass':
						highest_bidder = current_bidder

					if self.verbose != 'None':
						print("* Igralec", current_bidder, "je licitiral", last_bids[current_bidder])

			if last_bids[highest_bidder] == '3':									# zadnji v licitaciji lahko še licitira višje (ali enako)
				last_bids[highest_bidder] = self.players[highest_bidder].make_a_bid(BIDS[BIDS.index(last_bids[highest_bidder]):])
				#self.contract = random.choice(BIDS)
			else:
				last_bids[highest_bidder] = self.players[highest_bidder].make_a_bid(BIDS[BIDS.index(last_bids[highest_bidder]):-1])
				#self.contract = random.choice(BIDS[BIDS.index(last_bids[highest_bidder]):-1])

			if last_bids[highest_bidder] == 'pass':									# če so šli vsi naprej, se igra klop
				self.contract = 'klop'
				self.declarer = -1
			else:
				self.declarer = highest_bidder
				self.contract = last_bids[highest_bidder]
		else:
			self.contract = 'klop'
		return

	# declarer kliče kralja, s katerim bo igral - če mu to dopuščata število igralcev in contract
	def call_a_king(self):
		if (self.contract in SWITCH_SET) and (self.n_players == 4):
			self.king = self.players[self.declarer].call_a_king(self.contract)
		return

	# okolje določi time
	def determine_teams(self):
		if self.contract == 'klop':
			self.teams = ['team_A', 'team_B', 'team_C', 'team_D']
			self.teams = self.teams[:self.n_players]
		else:
			self.teams = ['team_B'] * self.n_players
			self.teams[self.declarer] = 'team_A'
			if (self.contract in SWITCH_SET) and (self.n_players == 4):
				partner = self.declarer
				for i in range(self.n_players):
					if self.king in self.hands[i]:
						partner = i
				self.teams[partner] = 'team_A'
		return

	# declarer zamenja karte s talonom, če to zahteva/dovoljuje contract
	def switch(self):
		if self.contract in SWITCH_SET:
			talon_set = iterutils.chunked(self.talon, SWITCH_SET[self.contract])		# razdelimo karte na skupine, ki jih declarer lahko zamenja
			self.cards_taken, self.cards_dropped = self.players[self.declarer].switch(talon_set, self.hands[self.declarer])
			self.hands[self.declarer] = [e for e in (self.hands[self.declarer] + self.cards_taken) if not e in self.cards_dropped]
			self.hands[self.declarer].sort(key = CARDS.index)
			self.talon = [e for e in self.talon if not e in self.cards_taken]
		return

	# odigra eno igro (torej vse runde ene epizode)
	def play(self):
		current_player = self.start_player
		rounds = 48 // self.n_players
		for i in range(rounds):
			trick = ['--'] * self.n_players
			trick_meta = [current_player]
			first_card_idx = current_player
			for j in range(self.n_players):
				trick[current_player] = self.players[current_player].play(self.hands[current_player], trick, self.contract, first_card_idx)
				self.hands[current_player].remove(trick[current_player])
				current_player = (current_player + 1) % self.n_players

			current_player = trick_winner(trick_meta[0], trick)
			trick_meta.append(current_player)
			if self.contract == 'klop':
				if self.talon != []:													# "priboljški" v primeru klopa
					trick.append(self.talon.pop())
				trick_meta.append(-count_points(trick))									# negativna vrednost štiha v primeru klopa
			else:
				trick_meta.append(count_points(trick))
			self.trick_pile.append(trick)
			self.trick_pile_meta.append(trick_meta)

			if self.verbose != 'None':
				print("* Round", i+1, trick, trick_meta)

			self.broadcast_message('trick', trick, message2=trick_meta)

		self.broadcast_message('end_of_episode', '', '')
		return

	# seštevek točk iz štihov za posameznega igralca: seštej točke iz štihov, združi točke timov, prišteje točke založenih kart
	def count(self):
		for i in range(len(self.trick_pile_meta)):									# sešteješ štihe vsakega posameznika
			self.trick_points[self.trick_pile_meta[i][1]] += self.trick_pile_meta[i][2]

		team_points = {'team_A': 0, 'team_B': 0, 'team_C': 0} 						# definiraš možne time
		if self.n_players == 4:
			team_points['team_D'] = 0

		for i in range(self.n_players):												# sešteješ točke -> točke timov iz štihov
			team_points[self.teams[i]] += self.trick_points[i]

		if self.contract != 'klop':
			if team_points['team_A'] == 0:											# ali je kdo naredil valata?
				self.bonus_dic['valat'] = ['team_B']
			if team_points['team_B'] == 0:
				self.bonus_dic['valat'] = ['team_A']

			team_points['team_A'] += count_points(self.cards_dropped)				# prišteješ še založene karte
			
			if (self.king in self.cards_taken):
				king_idx = [self.trick_pile.index(e) for e in self.trick_pile if self.king in e]
				king_idx = king_idx[0]
				if (self.trick_pile_meta[king_idx][1] == self.declarer):
					self.king_from_talon_passed = self.king in self.cards_taken		# declarer je vzel iz talona zarufanega kralja in ga "spravil okoli" ...
					team_points['team_A'] += count_points(self.talon)				# ... dobi preostanek talona
				else:
					team_points['team_B'] += count_points(self.talon)				# obrambnemu timu prišteješ točke preostanka talona
			else:
				team_points['team_B'] += count_points(self.talon)					# obrambnemu timu prišteješ točke preostanka talona
		else:
			for p in team_points:													# ali je kdo zmagal/zgubil klopa?
				if team_points[p] < -35:
					self.bonus_dic['klop70'].append(p)
				if team_points[p] == 0:
					self.bonus_dic['klop0'].append(p)
		
		self.trick_points = [int(round(team_points[e])) for e in self.teams]		# točke posameznika glede na tim
		return

	# uporabi seštevek točk iz štihov in izračuna končni rezultat ene igre.
	def score(self):
		def n_from_group(group, team):
			in_tricks = [e for e in self.trick_pile for c in e if c in group]			# naredi seznam vseh štihov s kartami skupin
			in_tricks = [self.trick_pile.index(e) for e in in_tricks]					# naredi seznam indeksov štihov s kartami skupine
			from_team = [self.teams[self.trick_pile_meta[i][1]] for i in in_tricks]		# seznam timov, ki so pobrali posamezno karto skupine
			
			if self.king_from_talon_passed:
				from_team += ['team_A' for c in group if c in self.talon]
			else:
				from_team += ['team_B' for c in group if c in self.talon]
			return from_team.count(team)

		if self.contract != 'klop':
			if self.bonus_dic['valat'] != []:														# korekcija rezultata glede na bonus pri valatu
				for i in range(self.n_players):															
					if self.teams[i] == self.teams[self.declarer]:
						if self.teams[i] in self.bonus_dic['valat']:
							self.total_score[i] = 250
						else:
							self.total_score[i] = -250
					else:
						self.total_score[i] = 0

			else: # ni valat
				# izračuna točke teama, ki je igral, na podlagi razlike do 35 v vsoti štihov in vrednosti igre
				if self.trick_points[self.declarer] > 35:											
					team_A_score = self.trick_points[self.declarer] - 35 + BIDS_VAL[self.contract]		# zmaga!
				else: 
					team_A_score = -(35 - self.trick_points[self.declarer]) - BIDS_VAL[self.contract]	# poraz!

				# preveri pagata ultimo in po potrebi doda/odvzame točke
				# +25 piše, če je vrgel pagata kdo iz tema, ki je igral in je isti igralec dobil zadnji štih, ali...
				# če je pagata vrgel kdo iz nasprotnega tima in je štih pobral kdo iz tima, ki igra.
				# v vseh drugih primerih tim, ki igra, piše -25
				if 'tI' in self.trick_pile[-1]:		# če je bil v zadnjem štihu pagat in...
					tI_played = self.trick_pile[-1].index('tI')
					tI_won = self.trick_pile_meta[-1][1]
					if (self.teams[tI_played] == 'team_A') and (tI_played == tI_won):
							team_A_score += 25
							self.bonus_dic['tI+'].append(self.teams[self.declarer])
					elif (self.teams[tI_played] == 'team_B') and (self.teams[tI_won] == 'team_A'):
							team_A_score += 25
							self.bonus_dic['tI+'].append(self.teams[self.declarer])
					else:
						team_A_score -= 25
						self.bonus_dic['tI-'].append(self.teams[self.declarer])

				# preveri kralja ultimo in po potrebi doda/odvzame točke
				if self.king in self.trick_pile[-1]:
					last_winner = self.trick_pile_meta[-1][1]
					if self.teams[last_winner] == 'team_A':
						team_A_score += 10
						self.bonus_dic['king+'].append(self.teams[self.declarer])
					else:
						team_A_score -= 10
						self.bonus_dic['king-'].append(self.teams[self.declarer])

				# preveri vse kralje
				k = n_from_group(['kK', 'sK', '+K', 'pK'], 'team_A')
				if k == 4:
					team_A_score += 10
					self.bonus_dic['king4'].append('team_A')
				elif k == 0:
					team_A_score -= 10
					self.bonus_dic['king4'].append('team_B')

				# preveri trulo
				k = n_from_group(['tI', 'tXXI', 'tS'], 'team_A')
				if k == 4:
					team_A_score += 10
					self.bonus_dic['trula3'].append('team_A')
				elif k == 0:
					team_A_score -= 10
					self.bonus_dic['trula3'].append('team_B')

				# pripravi končni rezultat glede na udeležbo v timu, ki je igral (team_A)
				for i in range(self.n_players):
					if self.teams[i] == 'team_A':
						self.total_score[i] = team_A_score

				# odšteje individualno točke za izgubljeno XXI
				if not('tXXI' in self.talon):				# XXI ni ostal v talonu
					for e in self.trick_pile:
						if 'tXXI' in e:
							trick_idx = self.trick_pile.index(e)						
					
					xxi_idx = self.trick_pile[trick_idx].index('tXXI')
					if (self.trick_pile_meta[trick_idx][1] != xxi_idx):
						self.total_score[xxi_idx] -= 21
						self.bonus_dic['tXXI-'].append(xxi_idx)

				elif not(self.king_from_talon_passed):		# XXI je ostal v talonu in zarufani kralj ni šel okoli ali pa niti ni bil zarufan
						self.total_score[self.declarer] -= 21
						self.bonus_dic['tXXI-'].append(self.declarer)			
		else: # je klop
			self.total_score = [e for e in self.trick_points]
			klop_0_70 = self.bonus_dic['klop0'] + self.bonus_dic['klop70']
			for i in range(self.n_players):															# korekcija rezultata glede na bonuse pri klopu
				if self.teams[i] in self.bonus_dic['klop0']:										# če je brez štiha...
					self.total_score[i] = 70
				if self.teams[i] in self.bonus_dic['klop70']:										# če ima več kot 35 točk...
					self.total_score[i] = -70 
				if (klop_0_70 != []) and not (self.teams[i] in klop_0_70):
					self.total_score[i] = 0

		for b in self.bonus_dic:
			if self.bonus_dic[b] != []:
				self.bonus_dic[b] = [e for e in range(len(self.teams)) if (self.teams[e] in self.bonus_dic[b]) or (e in self.bonus_dic[b])]
		return

	# obvesti vse igralce in izpiše sporočila, če mu to veleva verbose način
	def broadcast_message(self, info, message1, message2='', message3=''):
		for k in range(self.n_players):
			if info == 'hand':
				self.players[k].get_message(info, self.hands[k])
				if self.verbose == 'All':
					print("* Igralec", k, self.hands[k])
			elif info == 'cards_dropped':
				if self.declarer == k:
					self.players[k].get_message('cards_dropped', self.cards_dropped)
			else:
				self.players[k].get_message(info, message1, message2, message3)

		if self.verbose != 'None':
			if (info == 'declarer') and (message1 != -1):
				print("* Licitacijo je dobil igralec", message1)
			if info == 'contract':
				print("* Licitirana igra je", message1)
			if info == 'king':
				print("* Klican je bil kralj", message1)
			if info == 'talon':
				print("* Talon je odprt", message1)
			if info == 'cards_taken':
				print("* Iz talona so bile vzete karte", message1)
			if (info == 'cards_dropped') and (self.verbose == 'All'):
				print("* Založene so bile karte", message1)
			if info == 'teams':
				print("* Sestava timov", message1)
			if info == 'score':
				print("\n* Točke zadnje igre   ", message2)
				print("* Bonusi", message1)
				print("* Rezultat zadnje igre", self.total_score)
				print("")			
		return

	# odigra eno epizodo - z vsemi fazami - in izpiše igro za gledalca, če verbose == True
	def episode(self):
		self.reset()
		self.deal_cards()
		self.broadcast_message('hand', '')

		self.auction()
		self.broadcast_message('declarer', self.declarer)
		self.broadcast_message('contract', self.contract)

		if self.n_players == 4:
			self.call_a_king()
			self.broadcast_message('king', self.king)
		
		if self.contract != 'klop':
			self.broadcast_message('talon', self.talon)

		self.determine_teams()
		self.broadcast_message('teams', self.teams)
		self.switch()
		self.broadcast_message('cards_taken', self.cards_taken)
		self.broadcast_message('cards_dropped', self.cards_dropped)

		self.play()

		self.count()
		self.score()
		self.broadcast_message('score', self.bonus_dic, self.trick_points, self.total_score)
		return

	# isto kot episode(), je da zamenja karti c1 in c2
	def episode_swap(self, c1, c2):
		# zamenja c1 in c2
		def swap(c1, c2):
			for k in range(self.n_players):
				for i in range(len(self.hands[k])):
					if self.hands[k][i] == c1:
						self.hands[k][i] = c2
					elif self.hands[k][i] == c2:
						self.hands[k][i] = c1

			for i in range(len(self.talon)):
				if self.talon[i] == c1:
					self.talon[i] = c2
				elif self.talon[i] == c2:
					self.talon[i] = c1
			return

		self.reset()
		self.deal_cards()
		swap(c1, c2)
		self.broadcast_message('hand', '')

		self.auction()
		self.broadcast_message('declarer', self.declarer)
		self.broadcast_message('contract', self.contract)

		if self.n_players == 4:
			self.call_a_king()
			self.broadcast_message('king', self.king)
		
		if self.contract != 'klop':
			self.broadcast_message('talon', self.talon)

		self.determine_teams()
		self.broadcast_message('teams', self.teams)
		self.switch()
		self.broadcast_message('cards_taken', self.cards_taken)
		self.broadcast_message('cards_dropped', self.cards_dropped)

		self.play()

		self.count()
		self.score()
		self.broadcast_message('score', self.bonus_dic, self.trick_points, self.total_score)
		return

