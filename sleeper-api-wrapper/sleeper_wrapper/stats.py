from sleeper_wrapper.base_api import BaseApi

class Stats(BaseApi):
	def __init__(self):
		self._base_url = "https://api.sleeper.app/v1/stats/{}".format("nfl")
		self._projections_base_url = "https://api.sleeper.app/v1/projections/{}".format("nfl")
		self._full_stats = None

	def get_all_stats(self, season_type, season):
		return self._call("{}/{}/{}".format(self._base_url, season_type, season)) 

	def get_week_stats(self, season_type, season, week):
		return self._call("{}/{}/{}/{}".format(self._base_url, season_type, season, week))

	def get_all_projections(self, season_type, season):
		return self._call("{}/{}/{}".format(self._projections_base_url, season_type, season))

	def get_week_projections(self, season_type, season, week):
		return self._call("{}/{}/{}/{}".format(self._projections_base_url, season_type, season, week))

	def get_player_week_stats(self, stats, player_id, settings):
		try:
			return self.calculate_score_with_league_settings(stats, player_id, settings)[player_id]
		except Exception as e:
			return None


	def get_player_week_score(self, stats, player_id):
		#TODO: Need to cache stats by week, to avoid continuous api calls
		result_dict = {}
		try:
			player_stats = stats[player_id]
		except:
			return None

		if stats:
			try:
				result_dict["pts_ppr"] = player_stats["pts_ppr"]
			except:
				result_dict["pts_ppr"] = None

			try:
				result_dict["pts_std"] = player_stats["pts_std"]
			except:
				result_dict["pts_std"] = None

			try:
				result_dict["pts_half_ppr"] = player_stats["pts_half_ppr"]
			except:
				result_dict["pts_half_ppr"] = None

		return result_dict

	def calculate_score_with_league_settings(self, stats, player_id, settings):
		# uses a league's custom scoring settings to calculate a given player's score

		if player_id not in stats:
			return stats

		point_total = 0

		for stat, value in stats[player_id].items():
			if stat in settings:
				point_total += (value * (settings[stat]))

		stats[player_id]["pts_custom"] = point_total

		return stats
