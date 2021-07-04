import random
import time

from . import exceptions
from . import shared
from . import utilities

class Game:
	def __init__(self, group):
		""" Game object that stores information about the game, such as whether
		or not it is in progress, the group it belongs to, the round history,
		and when the next action will be

		:param group: the group that the game belongs to
		"""
		self.in_progress = False
		self.group = group
		self.teams = []
		self.rounds = []
		self.next_action = 0

		self.custom_words = []
		self.custom_words_only = False

		self.round_count = 4

		shared.games.append(self)

	@property
	def is_finished(self):
		""" Whether or not the game is finished """
		return len(self.rounds) == len(self.teams) * self.round_count and self.rounds[-1].finished

	def construct_teams(self):
		""" Randomly generate the teams """
		members = self.group.members.copy()
		random.shuffle(members)

		teams = []

		for i in range(0, int(len(members) / 2)):
			teams.append([members[(i * 2)], members[(i * 2) + 1]])

		return teams

	def current_team(self):
		""" Get the currently playing team """
		return self.teams[len(self.rounds) % len(self.teams)]

	def edit(self, round_count=None, wordlist=None):
		""" Edit information about the game """
		if round_count != None:
			if not round_count.isdigit():
				raise exceptions.ClientError('INVALID_TYPE')

			parsed_round_count = int(round_count)
			
			if not 0 < parsed_round_count < 10:
				raise exceptions.ClientError('INVALID_RANGE')

			self.round_count = parsed_round_count

		if wordlist != None:
			if not isinstance(wordlist, list):
				raise exceptions.ClientError('INVALID_TYPE')

			new_words = []
			for word in wordlist:
				sanitized_word = utilities.sanitize_string(word)

				if sanitized_word in {'', None}:
					continue

				if not 0 < len(sanitized_word) < 16:
					continue

				new_words.append(sanitized_word)

			if not 0 < len(new_words) < 50:
				raise exceptions.ClientError('INVALID_RANGE')

			self.custom_words = new_words

	async def start(self):
		""" Start the game """
		self.group.game = self
		self.group.in_game = True
		self.in_progress = True

		self.teams = self.construct_teams()

		await self.group.send(1, 'GAME_START', {
			'teams': [
				[x.as_safe_dict(), y.as_safe_dict()] for x, y in self.teams
			],
			'cooldown': 10
		})

		self.next_action = int(time.time()) + 10

	async def end(self):
		""" End the game """
		self.in_progress = False

		scores = [{
			'team': [x.as_safe_dict() for x in team],
			'score': 0}
		for team in self.teams]
		
		for g_round in self.rounds:
			scores[self.teams.index(g_round.team)]['score'] += g_round.score

		await self.group.send(1, 'GAME_END', {
			'scores': scores
		})

		shared.games.remove(self)