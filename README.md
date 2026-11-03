# Sadonia's Dalamud plugins

One custom repository for all of my FFXIV plugins. Add it once and every plugin shows up in the plugin installer.

## Add it

1. In game: `/xlsettings` → **Experimental** → **Custom Plugin Repositories**.
2. Add `https://raw.githubusercontent.com/sadoniaveletoria/DalamudPlugins/main/pluginmaster.json`, tick it, save.
3. `/xlplugins` → search for the plugin → Install.

## Plugins

| Plugin | What it does |
|---|---|
| [CraftBuddy](https://github.com/sadoniaveletoria/CraftBuddy) | Gets every material for a craft (retainers, mob drops, gathering, reduction, vendors) and crafts it with Artisan |
| [FateRunner](https://github.com/sadoniaveletoria/Faterunner) | Runs FATEs for Bicolor Gemstones or leveling |
| [MogFlix](https://github.com/sadoniaveletoria/MogFlix) | Shows what you're watching on Plex, in game |
| [Target Zoom](https://github.com/sadoniaveletoria/TargetZoom) | Right-click anyone and zoom the camera onto them |

## How it stays up to date

Each plugin lives in its own repo with its own releases and `repo.json`. Every 10 minutes (or on demand from the Actions
tab) a job here merges those into `pluginmaster.json`. To add a plugin, add its `repo.json` raw link to
`sources.txt`.
