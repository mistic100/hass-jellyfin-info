from typing import TypedDict

class SystemInfo(TypedDict):
    Version: str
    LocalAddress: str

class User(TypedDict):
    Id: str
    Name: str

class PlayState(TypedDict):
    IsPaused: bool

class NowPlayingItem(TypedDict):
    Id: str
    Type: str
    Name: str
    AlbumId: str
    Album: str
    AlbumArtist: str
    SeasonId: str
    SeriesName: str
    SeasonName: str

class Session(TypedDict):
    Id: str
    UserName: str
    PlayState: PlayState
    NowPlayingItem: NowPlayingItem

class JellyfinData():
    initialized: bool = False
    system: SystemInfo
    users: list[User]
    sessions: list[Session]
