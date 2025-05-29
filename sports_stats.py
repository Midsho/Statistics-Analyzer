import aiohttp
import asyncio
from config import MY_TOKEN
from config import URL
HEADERS = {"Authorization": MY_TOKEN}


class AllStatics:
    def __init__(self):
        self.teams = []
        self.matches = []
        self.players = []
        self.team_map = {}
        self.player_team_map = {}
        self.player_names = []

    async def load_data(self):
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            self.teams = await self.get_json(session, f"{URL}/teams")
            if not self.teams:
                print("Ошибка загрузки команд")
                return

            self.matches = await self.get_json(session, f"{URL}/matches")
            if not self.matches:
                print("Ошибка загрузки матчей")
                return

            await self.get_all_players(session)

            self.team_map = {team['name']: team for team in self.teams}
            for team in self.teams:
                for pid in team['players']:
                    self.player_team_map[pid] = team['id']

            self.prepare_player_names()

    async def get_json(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Ошибка {response.status} для {url}")
                    return None
        except Exception as res:
            print(f"Ошибка {url}: {res}")
            return None

    async def get_all_players(self, session):
        player_ids = set()
        for team in self.teams:
            player_ids.update(team['players'])

        tasks = []
        for player_id in player_ids:
            url = f"{URL}/players/{player_id}"
            tasks.append(self.get_json(session, url))

        self.players = await asyncio.gather(*tasks)

    def prepare_player_names(self):
        names = []
        for player in self.players:
            if player:
                name = player.get('name', '')
                surname = player.get('surname', '')
                full_name = f"{name} {surname}".strip()
                if full_name:
                    names.append(full_name)

        names.sort()
        self.player_names = names

    def print_all_players(self):
        for name in self.player_names:
            print(name)

    def get_team_stats(self, team_name):
        team = self.team_map.get(team_name)
        if not team:
            return (0, 0, 0)

        wins = 0
        loss = 0
        goals_scored = 0
        goals_conceded = 0

        for match in self.matches:
            if match['team1'] == team['id']:
                if match['team1_score'] > match['team2_score']:
                    wins += 1
                else:
                    loss += 1
                goals_scored += match['team1_score']
                goals_conceded += match['team2_score']
            elif match['team2'] == team['id']:
                if match['team2_score'] > match['team1_score']:
                    wins += 1
                else:
                    loss += 1
                goals_scored += match['team2_score']
                goals_conceded += match['team1_score']

        return (wins, loss, goals_scored - goals_conceded)

    def get_versus_two_player(self, first_player_id, second_player_id):
        team1 = self.player_team_map.get(first_player_id)
        team2 = self.player_team_map.get(second_player_id)

        if not team1 or not team2:
            return 0

        res = 0
        cur = {team1, team2}
        for match in self.matches:
            teams = {match['team1'], match['team2']}
            if cur == teams:
                res += 1
        return res


async def main():
    stats = AllStatics()
    await stats.load_data()

    stats.print_all_players()

    while True:
        try:
            query = await asyncio.to_thread(input, "Введите запрос: ")
            if query.startswith("stats? "):
                parts = query.split('"')
                if len(parts) >= 2:
                    team_name = parts[1]
                else:
                    team_name = query[7:].strip()

                result = stats.get_team_stats(team_name)
                print(f"{result[0]} {result[1]} {result[2]}")

            elif query.startswith("versus? "):
                parts = query.split()
                if len(parts) != 3:
                    print(0)
                    continue
                try:
                    p1 = int(parts[1])
                    p2 = int(parts[2])
                    print(stats.get_versus_two_player(p1, p2))
                except:
                    print(0)
            else:
                print("Неизвестный запрос")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    asyncio.run(main())