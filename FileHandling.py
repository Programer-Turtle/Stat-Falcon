import os
import ast

def SaveSetup(ServerID, Type, Data):
    Path = os.path.join("Servers", str(ServerID))
    if not (os.path.isdir(Path)):
        os.makedirs(os.path.join(Path))
    with open(os.path.join(Path, f"{Type}.json"), "w") as SettingFile:
        SettingFile.write(str(Data))

def GetSetup(ServerID, Type):
    try:
        path = os.path.join("Servers", str(ServerID), f"{Type}.json")
        if (os.path.isfile(path)):
            with open(path, "r") as SetUpFile:
                return ast.literal_eval(SetUpFile.read())
        else:
            return "NotSetup"
    except Exception as e:
        print(e)

def SaveRegisterSiege(ServerID, Platform, SiegeUsername, DiscordID):
    Data = {
        "ID":DiscordID,
        "Username":SiegeUsername,
        "Platform":Platform
    }
    DirectoryPath = os.path.join("Servers", str(ServerID), "SiegeData")
    if not(os.path.isdir(DirectoryPath)):
        os.makedirs(DirectoryPath)
    
    FilePath = os.path.join(DirectoryPath, f"{str(DiscordID)}.json")
    with open(FilePath, "w") as UserFile:
        UserFile.write(str(Data))

def GetAllSiegeServers():
    directory = os.path.join("Servers")
    ServerDirs = [os.path.join(directory,f) for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

    ServerList = []
    for severdir in ServerDirs:
        path = os.path.join(severdir, "siege.json")
        print(path)
        if(os.path.isfile(path)):
            Dictionary = {}
            with open(path, "r") as siegeFile:
                siegeDict = ast.literal_eval(siegeFile.read())
                Dictionary = {
                    'Server':siegeDict["Server"],
                    'Post':siegeDict["Post"],
                    "RankedLeaderboard":siegeDict["RankedLeaderboard"]
                    }
            Users = []
            UsersPath  = os.path.join("Servers", siegeDict["Server"], "SiegeData")
            UserFiles = [os.path.join(UsersPath,f) for f in os.listdir(UsersPath) if os.path.isfile(os.path.join(UsersPath, f))]
            for File in UserFiles:
                with open(File, "r") as DataFile:
                    Users.append(ast.literal_eval(DataFile.read()))
            Dictionary["Users"] = Users
            ServerList.append(Dictionary)
    
    return ServerList