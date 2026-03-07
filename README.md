# Home Assistant Jellyfin Info Integration

> [!NOTE]
> This is not a media player, use the [official integration](https://www.home-assistant.io/integrations/jellyfin) instead.

This integration connects to a Jellyfin server API to expose some data about the server.

The following sensors are available:

### User sessions

A binary sensor is created for each user registered on the server which is ON when the user has at least one active session (ie. a media is playing).

The sensor also has additional attributes:

- `type` ("Audio", "Episode", "Movie")
- `name`
- `parent_name` ("artist - album" for audio, "series - season" for episode)
- `cover_url`

All sensors are grouped under a single "Jellyfin Sessions" device.


## Installation

### HACS

The integration is available in [HACS](https://hacs.xyz/).
      
1. **Install the Integration**:

    Simply click on the button to open the repository in HACS or search for "Jellyfin Info" and download it through the UI.

    [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mistic100&repository=hass-jellyfin-info&category=integration)

2. **Restart Home Assistant**:

    * Go to **Settings > System** and click the **Restart** button.

3. **Add the Integration**:

    * Go to **Settings > Devices & Services > Add Integration**
    * Search for and select **Jellyfin Info**

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/mistic100/hass-jellyfin-info/releases)
2. Extract the `jellyfin_info` folder to your `custom_components` directory
3. Restart Home Assistant
4. Go to **Settings > Devices & Services > Add Integration**
5. Search for and select **Jellyfin Info**.


## Configuration

Configuration is done via the UI. Multiple servers can be added (untested). You will need to provide the server URL and your access token (go to "Settings > Advanced > API keys" to create a new token).


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
