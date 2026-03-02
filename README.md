# Home Assistant Jellyfin Info Integration

> [!NOTE]
> This is not a media player, use the [official integration](https://www.home-assistant.io/integrations/jellyfin) instead.

This integration connects to a Jellyfin server API to expose some data about the server.

The following sensors are available:

- user sessions

### User sessions

A binary sensor is created for each user registered on the server which is ON when the user has at least one active session (ie. a media is playing).

The sensor also has additional attributes:

- `type` ("Audio", "Episode", "Movie")
- `name`
- `parent_name` ("artist - album" for audio, "series - season" for episode)
- `cover_url`

All sensors are grouped under a single "Jellyfin Sessions" device.

---

## Installation

This integration is best installed via the [Home Assistant Community Store (HACS)](https://hacs.xyz/).

### HACS (Recommended)

1. **Add the Custom Repository**:
    * Ensure HACS is installed.
    * Go to **HACS > Integrations > ... (three dots) > Custom repositories**.
    * Add this repository's URL: `https://github.com/mistic100/hass-jellyfin-info`
    * Select the category **Integration** and click **Add**.
      
2. **Install the Integration**:
    * In HACS, search for "Jellyfin Info" and click **Download**.
    * Follow the prompts to complete the download.

3. **Restart Home Assistant**:
    * Go to **Settings > System** and click the **Restart** button.

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/mistic100/hass-jellyfin-info/releases)
2. Extract the `jellyfin_info` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

Configuration is done via the UI. Multiple servers can be added (untested). You will need to provide the server URL and your access token (go to "Settings > Advanced > API keys" to create a new token).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
