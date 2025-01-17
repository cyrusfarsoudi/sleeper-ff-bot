import schedule
import time
import datetime as dt
import os
import pendulum
from discord import Discord
from sleeper_wrapper import League, Stats, Players, State

"""
These are all of the utility functions.
"""


def get_league_scoreboards(league_id, week):
    """
    Returns the scoreboards from the specified sleeper league.
    :param league_id: Int league_id
    :param week: Int week to get the scoreboards of
    :return: dictionary of the scoreboards; https://github.com/SwapnikKatkoori/sleeper-api-wrapper#get_scoreboards
    """
    league = League(league_id)
    matchups = league.get_matchups(week)
    users = league.get_users()
    rosters = league.get_rosters()
    scoreboards = league.get_scoreboards(rosters, matchups, users, "pts_custom", week)
    return scoreboards


def get_highest_score(league_id):
    """
    Gets the highest score of the week
    :param league_id: Int league_id
    :return: List [score, team_name]
    """
    week = get_current_week()
    scoreboards = get_league_scoreboards(league_id, week)
    max_score = [0, None]

    for matchup_id in scoreboards:
        matchup = scoreboards[matchup_id]
        # check both teams in the matchup to see if they have the highest score in the league
        if float(matchup[0][1]) > max_score[0]:
            score = matchup[0][1]
            team_name = matchup[0][0]
            max_score[0] = score
            max_score[1] = team_name
        if float(matchup[1][1]) > max_score[0]:
            score = matchup[1][1]
            team_name = matchup[1][0]
            max_score[0] = score
            max_score[1] = team_name
    return max_score


def get_lowest_score(league_id):
    """
    Gets the lowest score of the week
    :param league_id: Int league_id
    :return: List[score, team_name]
    """
    week = get_current_week()
    scoreboards = get_league_scoreboards(league_id, week)
    min_score = [999, None]

    for matchup_id in scoreboards:
        matchup = scoreboards[matchup_id]
        # check both teams in the matchup to see if they have the lowest score in the league
        if float(matchup[0][1]) < min_score[0]:
            score = matchup[0][1]
            team_name = matchup[0][0]
            min_score[0] = score
            min_score[1] = team_name
        if float(matchup[1][1]) < min_score[0]:
            score = matchup[1][1]
            team_name = matchup[1][0]
            min_score[0] = score
            min_score[1] = team_name
    return min_score


def make_roster_dict(starters_list, bench_list):
    """
    Takes in a teams starter list and bench list and makes a dictionary with positions.
    :param starters_list: List of a teams starters
    :param bench_list: List of a teams bench players
    :return: {starters:{position: []} , bench:{ position: []} }
    """
    week = get_current_week()
    players = Players().get_all_players()
    stats = Stats()
    state = State()
    week_stats = stats.get_week_stats("regular", state.get_season_start_year(), week)

    roster_dict = {"starters": {}, "bench": {}}
    for player_id in starters_list:
        player = players[player_id]
        player_position = player["position"]
        player_name = player["first_name"] + " " + player["last_name"]
        try:
            player_std_score = week_stats[player_id]["pts_custom"]
        except KeyError:
            player_std_score = None

        player_and_score_tup = (player_name, player_std_score)
        if player_position not in roster_dict["starters"]:
            roster_dict["starters"][player_position] = [player_and_score_tup]
        else:
            roster_dict["starters"][player_position].append(player_and_score_tup)

    for player_id in bench_list:
        player = players[player_id]
        player_position = player["position"]
        player_name = player["first_name"] + " " + player["last_name"]

        try:
            player_std_score = week_stats[player_id]["pts_custom"]
        except KeyError:
            player_std_score = None

        player_and_score_tup = (player_name, player_std_score)
        if player_position not in roster_dict["bench"]:
            roster_dict["bench"][player_position] = [player_and_score_tup]
        else:
            roster_dict["bench"][player_position].append(player_and_score_tup)

    return roster_dict


def get_highest_bench_points(bench_points):
    """
    Returns a tuple of the team with the highest scoring bench
    :param bench_points: List [(team_name, std_points)]
    :return: Tuple (team_name, std_points) of the team with most std_points
    """
    max_tup = ("team_name", 0)
    for tup in bench_points:
        if tup[1] > max_tup[1]:
            max_tup = tup
    return max_tup


def map_users_to_team_name(users):
    """
    Maps user_id to team_name
    :param users:  https://docs.sleeper.app/#getting-users-in-a-league
    :return: Dict {user_id:team_name}
    """
    users_dict = {}

    # Maps the user_id to team name for easy lookup
    for user in users:
        try:
            users_dict[user["user_id"]] = user["metadata"]["team_name"]
        except:
            users_dict[user["user_id"]] = user["display_name"]
    return users_dict


def map_roster_id_to_owner_id(league_id):
    """

    :return: Dict {roster_id: owner_id, ...}
    """
    league = League(league_id)
    rosters = league.get_rosters()
    result_dict = {}
    for roster in rosters:
        roster_id = roster["roster_id"]
        owner_id = roster["owner_id"]
        result_dict[roster_id] = owner_id

    return result_dict


def get_bench_points(league_id):
    """

    :param league_id: Int league_id
    :return: List [(team_name, score), ...]
    """
    week = get_current_week()

    league = League(league_id)
    scoring_settings = league.get_league_scoring_settings()
    users = league.get_users()
    matchups = league.get_matchups(week)

    stats = Stats()
    state = State()
    # WEEK STATS NEED TO BE FIXED
    week_stats = stats.get_week_stats("regular", state.get_season_start_year(), week)

    owner_id_to_team_dict = map_users_to_team_name(users)
    roster_id_to_owner_id_dict = map_roster_id_to_owner_id(league_id)
    result_list = []

    for matchup in matchups:
        starters = matchup["starters"]
        all_players = matchup["players"]
        bench = set(all_players) - set(starters)

        socal_points = 0
        for player in bench:
            try:
                socal_points += stats.get_player_week_stats(week_stats, player, scoring_settings)["pts_custom"]
            except:
                continue
        owner_id = roster_id_to_owner_id_dict[matchup["roster_id"]]
        if owner_id is None:
            team_name = "Team name not available"
        else:
            team_name = owner_id_to_team_dict[owner_id]
        result_list.append((team_name, socal_points))

    return result_list


def get_negative_starters(league_id):
    """
    Finds all of the players that scores negative points in standard and
    :param league_id: Int league_id
    :return: Dict {"owner_name":[("player_name", std_score), ...], "owner_name":...}
    """
    week = get_current_week()

    league = League(league_id)
    users = league.get_users()
    matchups = league.get_matchups(week)

    stats = Stats()
    state = State()
    # WEEK STATS NEED TO BE FIXED
    week_stats = stats.get_week_stats("regular", state.get_season_start_year(), week)

    players = Players()
    players_dict = players.get_all_players()
    owner_id_to_team_dict = map_users_to_team_name(users)
    roster_id_to_owner_id_dict = map_roster_id_to_owner_id(league_id)

    result_dict = {}

    for i, matchup in enumerate(matchups):
        starters = matchup["starters"]
        negative_players = []
        for starter_id in starters:
            try:
                std_pts = week_stats[str(starter_id)]["pts_custom"]
            except KeyError:
                std_pts = 0
            if std_pts < 0:
                player_info = players_dict[starter_id]
                player_name = "{} {}".format(player_info["first_name"], player_info["last_name"])
                negative_players.append((player_name, std_pts))

        if len(negative_players) > 0:
            owner_id = roster_id_to_owner_id_dict[matchup["roster_id"]]

            if owner_id is None:
                team_name = "Team name not available" + str(i)
            else:
                team_name = owner_id_to_team_dict[owner_id]
            result_dict[team_name] = negative_players
    return result_dict


def check_starters_and_bench(lineup_dict):
    """

    :param lineup_dict: A dict returned by make_roster_dict
    :return:
    """
    for key in lineup_dict:
        pass


def get_current_week():
    """
    Gets the current week.
    :return: Int current week
    """
    today = pendulum.today()
    state = State()
    starting_week = pendulum.datetime(state.get_season_start_year(), state.get_season_start_month(), state.get_season_start_day())
    week = today.diff(starting_week).in_weeks()
    return week + 1


"""
These are all of the functions that create the final strings to send.
"""


def get_welcome_string():
    """
    Creates and returns the welcome message
    :return: String welcome message
    """
    state = State()
    welcome_message = "👋 Hello, I am Sleeper Bot! \n\nThe bot schedule for the {} ff season can be found here: ".format(
        state.get_season_start_year())
    welcome_message += "https://github.com/cyrusfarsoudi/sleeper-ff-bot#current-schedule \n\n"
    welcome_message += "Any feature requests, contributions, or issues for the bot can be added here: " \
                       "https://github.com/cyrusfarsoudi/sleeper-ff-bot \n\n"

    return welcome_message


def send_any_string(string_to_send):
    """
    Send any string to the bot.
    :param string_to_send: The string to send a bot
    :return: string to send
    """
    return string_to_send


def get_matchups_string(league_id):
    """
    Creates and returns a message of the current week's matchups.
    :param league_id: Int league_id
    :return: string message of the current week mathchups.
    """
    week = get_current_week()
    scoreboards = get_league_scoreboards(league_id, week)
    final_message_string = "**===============================**\n"
    final_message_string += "**Matchups for Week {}**\n".format(week)
    final_message_string += "**===============================**\n\n"

    for i, matchup_id in enumerate(scoreboards):
        matchup = scoreboards[matchup_id]
        matchup_string = "*Matchup {}*:\n".format(i + 1)
        matchup_string += "**{}** vs. **{}** \n\n".format(matchup[0][0], matchup[1][0])
        final_message_string += matchup_string

    return final_message_string


def get_playoff_bracket_string(league_id):
    """
    Creates and returns a message of the league's playoff bracket.
    :param league_id: Int league_id
    :return: string message league's playoff bracket
    """
    league = League(league_id)
    bracket = league.get_playoff_winners_bracket()
    return bracket


def get_scores_string(league_id):
    """
    Creates and returns a message of the league's current scores for the current week.
    :param league_id: Int league_id
    :return: string message of the current week's scores
    """
    week = get_current_week()
    scoreboards = get_league_scoreboards(league_id, week)
    final_message_string = "**================================**\n"
    final_message_string += "**Scores**\n"
    final_message_string += "**================================**\n\n"
    for i, matchup_id in enumerate(scoreboards):
        matchup = scoreboards[matchup_id]
        first_score = ""
        second_score = 0
        if matchup[0][1] is not None:
            first_score = '{0:.2f}'.format(matchup[0][1]) + " (" + '{0:.2f}'.format(matchup[0][2]) + ")"
        if matchup[1][1] is not None:
            second_score = '{0:.2f}'.format(matchup[1][1]) + " (" + '{0:.2f}'.format(matchup[1][2]) + ")"
        string_to_add = "*Matchup {}*\n**{}** {}\n**{}** {}\n\n".format(i + 1, matchup[0][0], first_score,
                                                                                matchup[1][0], second_score)
        final_message_string += string_to_add

    return final_message_string


def get_close_games_string(league_id, close_num):
    """
    Creates and returns a message of the league's close games.
    :param league_id: Int league_id
    :param close_num: Int what poInt difference is considered a close game.
    :return: string message of the current week's close games.
    """
    league = League(league_id)
    week = get_current_week()
    scoreboards = get_league_scoreboards(league_id, week)
    close_games = league.get_close_games(scoreboards, close_num)

    final_message_string = "**================================**\n"
    final_message_string += "**Close games**\n"
    final_message_string += "**================================**\n\n"

    for i, matchup_id in enumerate(close_games):
        matchup = close_games[matchup_id]
        string_to_add = "*Matchup {}*\n**{} {:.2f}** ({:.2f})\n**{} {:.2f}** ({:.2f})\n\n".format(i + 1, matchup[0][0], matchup[0][1], matchup[0][2],
                                                                                matchup[1][0], matchup[1][1], matchup[1][2])
        final_message_string += string_to_add
    return final_message_string


def get_standings_string(league_id):
    """
    Creates and returns a message of the league's standings.
    :param league_id: Int league_id
    :return: string message of the leagues standings.
    """
    league = League(league_id)
    rosters = league.get_rosters()
    users = league.get_users()
    standings = league.get_standings(rosters, users)
    final_message_string = "**================================**\n"
    final_message_string += "**Standings **\n"
    final_message_string += "**================================**\n\n"
    try:
        playoff_line = os.environ["NUMBER_OF_PLAYOFF_TEAMS"] - 1
    except:
        playoff_line = 5
    for i, standing in enumerate(standings):
        team = standing[0]
        if team is None:
            team = "Team NA"
        string_to_add = "**{}. {}** ({}-{}) *{} points*\n".format(i + 1, team, standing[1], standing[2], standing[3])
        if i == playoff_line:
            string_to_add += "================================\n"
        final_message_string += string_to_add
    return final_message_string


def get_best_and_worst_string(league_id):
    """
    :param league_id: Int league_id
    :return: String of the highest Scorer, lowest scorer, most points left on the bench, and Why bother section.
    """
    final_message_string = "**================================**\n"
    final_message_string += "**Highlights**\n"
    final_message_string += "**================================**\n\n"

    highest_scorer = get_highest_score(league_id)[1]
    highest_score = get_highest_score(league_id)[0]
    highest_score_emojis = "<a:eggplantjerkoff:887917138394902530>"
    lowest_scorer = get_lowest_score(league_id)[1]
    lowest_score = get_lowest_score(league_id)[0]
    lowest_score_emojis = "<:KekYou:741822317419823244>"
    final_message_string += "{} **Highest Scorer** {}\n{}\n*{:.2f}*\n\n{} **Lowest Scorer** {}\n{}\n*{:.2f}*\n\n".format(highest_score_emojis,
                                                                                                 highest_score_emojis,
                                                                                                 highest_scorer,
                                                                                                 highest_score,
                                                                                                 lowest_score_emojis,
                                                                                                 lowest_score_emojis,
                                                                                                 lowest_scorer,
                                                                                                 lowest_score)
    highest_bench_score_emojis = "<:kekw:887913461294723182>"
    bench_points = get_bench_points(league_id)
    largest_scoring_bench = get_highest_bench_points(bench_points)
    final_message_string += "{} **Most points left on the bench** {}\n{}\n*{:.2f}*\n\n".format(highest_bench_score_emojis,
                                                                                           highest_bench_score_emojis,
                                                                                           largest_scoring_bench[0],
                                                                                           largest_scoring_bench[1])
    negative_starters = get_negative_starters(league_id)
    if negative_starters:
        final_message_string += "🤔🤔Why bother?\n"

    for key in negative_starters:
        negative_starters_list = negative_starters[key]
        final_message_string += "{} Started:\n".format(key)
        for negative_starter_tup in negative_starters_list:
            final_message_string += "{} who had {} in standard\n".format(negative_starter_tup[0], negative_starter_tup[1])
        final_message_string += "\n"
    return final_message_string


def get_bench_beats_starters_string(league_id):
    """
    Gets all bench players that outscored starters at their position.
    :param league_id: Int league_id
    :return: String teams which had bench players outscore their starters in a position.
    """
    week = get_current_week()
    league = League(league_id)
    matchups = league.get_matchups(week)

    final_message_string = "________________________________\n"
    final_message_string += "Worst of the week💩💩\n"
    final_message_string += "________________________________\n\n"

    for matchup in matchups:
        starters = matchup["starters"]
        all_players = matchup["players"]
        bench = set(all_players) - set(starters)

def process_transactions(league_id, players, bot, time_delta=60):
    week = get_current_week()
    league = League(league_id)
    transactions = league.get_transactions(week)
    users = league.get_users()

    owner_id_to_team_dict = map_users_to_team_name(users)
    roster_id_to_owner_id_dict = map_roster_id_to_owner_id(league_id)

    for t in transactions:
        transaction_time = t["created"] // 1000
        if dt.datetime.now().timestamp() - transaction_time > time_delta:
            continue

        # need to wait to have trade data to develop against
        if t["type"] == "trade":
            continue

        added_player_names = []
        dropped_player_names = []
        team_name = ""

        roster_id = t["roster_ids"][0]
        owner_id = roster_id_to_owner_id_dict[roster_id]
        team_name = owner_id_to_team_dict[owner_id]

        adds = t["adds"]
        drops = t["drops"]

        if adds:
            for player_id in adds.keys():
                added_player_names.append(players[player_id]["first_name"] + " " + players[player_id]["last_name"])

        if drops:
            for player_id in drops.keys():
                dropped_player_names.append(players[player_id]["first_name"] + " " + players[player_id]["last_name"])

        final_message_string = "**================================**\n"
        final_message_string += "**Transaction **\n"
        final_message_string += "**================================**\n"
        final_message_string += f"**{team_name}**"
        if t["type"] == "waiver":
            bid = t["settings"]["waiver_bid"]
            final_message_string += f" (*${bid}*)"

        for added_player in added_player_names:
            final_message_string += f"\n+ {added_player}"
        for dropped_player in dropped_player_names:
            final_message_string += f"\n- {dropped_player}"

        bot.send_message(final_message_string)


if __name__ == "__main__":
    """
    Main script for the bot
    """
    bot = None

    league_id = os.environ["LEAGUE_ID"]

    # Check if the user specified the close game num. Default is 20.
    try:
        close_num = os.environ["CLOSE_NUM"]
    except:
        close_num = 20

    state = State()
    starting_date = pendulum.datetime(state.get_season_start_year(), state.get_season_start_month(), state.get_season_start_day())


    webhook = os.environ["DISCORD_WEBHOOK"]
    bot = Discord(webhook)

    players = Players()
    players_dict = players.get_all_players()

    # bot.send(get_welcome_string)  # inital message to send
    schedule.every(1).minute.do(process_transactions, league_id, players_dict, bot)
    schedule.every().thursday.at("19:00").do(bot.send, get_matchups_string,
                                             league_id)  # Matchups Thursday at 4:00 pm PT
    schedule.every().friday.at("12:00").do(bot.send, get_scores_string, league_id)  # Scores Friday at 9 am PT
    schedule.every().sunday.at("23:00").do(bot.send, get_close_games_string, league_id,
                                           int(close_num))  # Close games Sunday on 4:00 pm PT
    schedule.every().monday.at("12:00").do(bot.send, get_scores_string, league_id)  # Scores Monday at 9 am PT
    schedule.every().tuesday.at("15:00").do(bot.send, get_standings_string,
                                            league_id)  # Standings Tuesday at 8:00 am PT
    schedule.every().tuesday.at("15:01").do(bot.send, get_best_and_worst_string,
                                            league_id)  # Standings Tuesday at 8:01 am PT

    while True:
        if starting_date <= pendulum.today():
            schedule.run_pending()
        time.sleep(50)
