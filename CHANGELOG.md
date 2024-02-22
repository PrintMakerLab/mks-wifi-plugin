# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/PrintMakerLab/mks-wifi-plugin/compare/1.4.5...HEAD)

<!-- Please do not update the unreleased notes. -->
<!-- Content should be placed here -->

## [1.4.5](https://github.com/PrintMakerLab/draft-repository/compare/1.4.4...1.4.5) - 2024-02-21

# What's Changed

## Bug Fixes

- fix: prevent preview from being disabled when printer selected @Jeredian (#405)
- fix: change initialization of `simage` and `gimage` variables @Jeredian (#404)

## Maintenance

- ci: validate pull request labels  @Jeredian (#396)

## Documentation

- docs: update issue templates @Jeredian (#398)

**Full Changelog**: https://github.com/PrintMakerLab/mks-wifi-plugin/compare/1.4.4...1.4.5


## [1.4.4](https://github.com/PrintMakerLab/draft-repository/compare/1.4.3...1.4.4) - 2024-02-08

# What's Changed

## New

- [MWP-366] feat: support model preview for Elegoo Neptune and Artillery Sidewinder series @Jeredian (#391)

**Full Changelog**: https://github.com/PrintMakerLab/mks-wifi-plugin/compare/1.4.3...1.4.4


## [1.4.3](https://github.com/PrintMakerLab/draft-repository/compare/1.4.3...1.4.4) - 2023-11-28

# What's Changed

## New

- [MWP-369] Port for connection added @Elkin-Vasily (#374)

## Bug Fixes

- [MWP-372] fix "Binding loop" warnings @Jeredian (#384)

## Maintenance

- [CI] Translation update @github-actions (#378)

## Dependency Updates

- [MWP-379] Support the 8.6.0 version of SDK for Cura 5.6.x @Jeredian (#382)

## Community

- Remove unneeded qmlregister type @nallath (#375)
- Add description to explain Drive Prefix @bobafetthotmail (#377)

**Full Changelog**: https://github.com/PrintMakerLab/mks-wifi-plugin/compare/1.4.2...1.4.3


## [1.4.2](https://github.com/PrintMakerLab/draft-repository/compare/1.4.3...1.4.4) - 2022-11-27

# What's Changed

## New

- [MWP-358] Drive prefix feature added @Elkin-Vasily (#360)
- [MWP-353] Cyrrilic filename rename @Elkin-Vasily (#355)
- [MWP-344] Check SD card message @Elkin-Vasily (#348)

## Bug Fixes

- [MWP-286] Delete/print file fix @Elkin-Vasily (#356)
- [MWP-341] Printer reboot while print starts fix @Elkin-Vasily (#342)

## Maintenance

- [MWP-337] Issue templates fixes @Elkin-Vasily (#338)

## Dependency Updates

- Support the 8.2.0 version of SDK for Cura 5.2+ @Jeredian

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.4.1...1.4.2



## [1.4.1](https://github.com/PrintMakerLab/draft-repository/compare/1.4.3...1.4.4) - 2022-07-07

# What's Changed

## New

- [MWP-282] Monitor Tab autoopen setting added @Elkin-Vasily (#317)

## Bug Fixes

- [MWP-316] Continuous reconnection fix @Elkin-Vasily (#321)
- [MWP-318] Monitor tab auto open fix @Elkin-Vasily (#319)

## Maintenance

- [MWP-328] Fix sonarqube code smells @Jeredian (#329)
- [MWP-322] Update feature labels for versioning @Jeredian (#327)
- [MWP-309] Translation workflow with PR @Elkin-Vasily (#325)
- [CI] Translation update @github-actions (#326)

## Documentation

- [MWP-305] Readme update @Elkin-Vasily (#323)

## Dependency Updates

- [MWP-332] Support the 8.1.0 version of SDK for Cura 5.1+ @Jeredian (#333)

## Community

- Add es_ES locale @JPBarrio (#324)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.4.0...1.4.1


## [1.4.0](https://github.com/PrintMakerLab/draft-repository/compare/1.3.2...1.4.0) - 2022-05-31

# What's Changed

## New

- [MWP-302] Translation autogen @Elkin-Vasily (#304)

## Bug Fixes

- [MWP-271] Reset old settings after plugin updated @Jeredian (#310)
- [MWP-301] Visual fixes @Elkin-Vasily (#306)
- [MWP-235] Print autostart checkbox added to plugin settings @Elkin-Vasily (#285)

## Maintenance

- Add .curapackage support @Jeredian (#307)

## Dependency Updates

- [MWP-287] Support new Cura 5.0 updates @Elkin-Vasily (#293)

## Other changes

- Qt6 migration - pt2 @ParkerK (#292)
- Qt6 migration @ParkerK (#288)
- Fix the infinite connect / disconnect loop @ParkerK (#290)
- [MWP-283] German translation added @Elkin-Vasily (#284)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.3.2...1.4.0


## [1.3.2](https://github.com/PrintMakerLab/draft-repository/compare/1.3.1...1.3.2) - 2022-02-20

# What's Changed

## Bug Fixes

- [MWP-276] Cura crashed with error: 'NoneType' object has no attribute 'getMetaDataEntry' @Jeredian (#277)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.3.1...1.3.2


## [1.3.1](https://github.com/PrintMakerLab/draft-repository/compare/1.3.0...1.3.1) - 2022-02-06

# What's Changed

## Bug Fixes

- [MWP-269] Crash Cura when printer connection state changed @Jeredian (#270)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.3.0...1.3.1


## [1.3.0](https://github.com/PrintMakerLab/draft-repository/compare/1.3.0...1.3.1) - 2022-01-23

# What's Changed

## New

- [MWP-232] Preview parameters for Wanhao D12 added @Elkin-Vasily (#238)

## Bug Fixes

- [MWP-58] Plugin functions rewritten @Elkin-Vasily (#257)
- [MWP-253] Wanhao D12 index fix @Elkin-Vasily (#254)
- [MWP-244] Monitor tab alignement fix @Elkin-Vasily (#245)
- [MWP-129] Connection procedure when printer start before Cura fix @Elkin-Vasily (#236)

## Maintenance

- [MWP-266] Add "type: community" label to the versioning @Jeredian (#267)
- [MWP-248] Add codeowners file @Jeredian (#264)
- [MWP-251] Zeroconf removed @Elkin-Vasily (#252)

## Dependency Updates

- [MWP-261] Support the 7.9.0 version of SDK for Cura 4.13.0+ @Jeredian (#263)
- [MWP-255] Arachne beta 2 support added @Elkin-Vasily (#256)

## Other changes

- [CPR] Add Auto File Renaming feature @alexandr-vladimirov (#262)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.2.6...1.3.0


## [1.2.6](https://github.com/PrintMakerLab/draft-repository/compare/1.2.5...1.2.6) - 2021-11-27

## What's Changed
* [MWP-207] [DEV] Release 1.2.6-dev by @Jeredian in https://github.com/Jeredian/mks-wifi-plugin/pull/209
* [MWP-212] Wrong printing time by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/213
* [MWP-214] Wrong printer model on screenshot tab by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/215
* [MWP-199] IP list fix by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/217
* [MWP-175] Selected IP did not remove when WiFi support turns off by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/216
* [MWP-218] Support the 7.8.0 version of SDK for Cura 4.12 by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/219
* [MWP-211] Saving as TFT file for a .ufp file comes with an error fixed by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/220
* [MWP-115] [BUG]1.2.0 MKS WiFi Delete file fails by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/221
* [MWP-222] QNetworkAccessManager changed by Uranium HttpRequestManager by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/223
* [MWP-224] Monitor tab print progress bar by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/225
* [MWP-228] File transfer cancel error fix by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/229
* [MWP-226] Preview adds on postprocessing by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/227
* [MWP-230] UnifiedConnectionState replaced with ConnectionState by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/231
* [MWP-210] [DEV] Release 1.2.6 by @Jeredian in https://github.com/Jeredian/mks-wifi-plugin/pull/237


**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.2.5...1.2.6


## [1.2.5](https://github.com/PrintMakerLab/draft-repository/compare/1.2.4...1.2.5) - 2021-10-07

## What's Changed
* [MWP-193] [DEV] Release 1.2.5-dev by @Jeredian in https://github.com/Jeredian/mks-wifi-plugin/pull/195
* [MWP-197] [FEATURE] Plugin compatibility with next Cura versions by @Jeredian in https://github.com/Jeredian/mks-wifi-plugin/pull/202
* [MWP-198] [FEATURE] Update Readme and issue templates by @Elkin-Vasily in https://github.com/Jeredian/mks-wifi-plugin/pull/203
* [MWP-201] [BUG] [1.2.4] It doesn't work well with Cura 4.11.0 by @Jeredian in https://github.com/Jeredian/mks-wifi-plugin/pull/205
* [MWP-206] [DEV] Release 1.2.5 by @Jeredian in https://github.com/Jeredian/mks-wifi-plugin/pull/208


**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.2.4...1.2.5


## [1.2.4](https://github.com/PrintMakerLab/draft-repository/compare/1.2.3...1.2.4) - 2021-08-15

It's a minor release with code optimization changes and API support updates. To update the plugin on the **Cura Marketplace**.

> Since this release, Cura versions 4.6 or 4.5 are no longer supported by plugin. (#190)
> Please update to the latest version of Cura, or use plugin version [1.2.2](https://github.com/Jeredian/mks-wifi-plugin/releases/tag/1.2.2).


### Features

- [FEATURE] Cognitive Complexity issue #94
- [FEATURE] Cognitive Complexity issue #188

### Bugfixes
- [BUG] Cura.ScrollView not working at Cura versions lower than 4.7 #190

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.2.3...1.2.4


## [1.2.3](https://github.com/PrintMakerLab/draft-repository/compare/1.2.2...1.2.3) - 2021-08-06

### Features

- [FEATURE] Restore correct license headers and clean up old files #164
- [FEATURE] Cura SDK minor version increase (7.5.0 -> 7.6.0) #171
- [FEATURE] Change max file name length from settings #172

### Bugfixes
- [BUG] Image setting is hidden before IP address added #136. (**NEW UI**)
- [BUG] Preview image preset can't be changed #163

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.2.2...1.2.3


## [1.2.2](https://github.com/PrintMakerLab/draft-repository/compare/1.2.1...1.2.2) - 2021-04-25

This release will contain updates to support new versions for Cura and Cura Arachne Engine:

* MWP-148 [FEATURE] Support Cura 4.9 (#155)
* CPR-140 Support Cura Arachne Engine beta version (#140)


**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.2.1...1.2.2


## [1.2.1](https://github.com/PrintMakerLab/draft-repository/compare/1.2.0...1.2.1) - 2021-03-01

New Features:
* MWP-80 [FEATURE] Can you add support without preview for TFT32  (#106)
* MWP-96 [FEATURE] Support Italian language (#102)
* MWP-98 [FEATURE] Support Chinese language (#101)
* MWP-107 [FEATURE] Implement model image size configuration (#130)

Bug Fixes: 
* MWP-11 The model preview in does not work correctly  (#106)
* MWP-45 Wrong Preview (#106)
* MWP-95 [BUG] 1.2.0 does not start on arachne engine (#103)
* MWP-99 [BUG] Button alignment fix on Monitor tab for different languages (#100)
* MWP-108 Incorrect size of "image setup" popup at windows (#109)
* MWP-114 [BUG]1.2.0 MKS WiFi fails to detect arbitrary extensions (#119)
* MWP-116 [BUG] 1.2.0 Changing name of duplicated file name fails (#118)
* MWP-125 Time left timer fix (#126)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.2.0...1.2.1


## [1.2.0](https://github.com/PrintMakerLab/draft-repository/compare/1.1.2...1.2.0) - 2021-02-01

* MWP-87 Fix sonarqube code smells (#92)
* MWP-90 Some i18n corrections. (#91)
* MWP-79 Double extruder  (#88)
* MWP-84 Add sonarqube badges and code check support (#86)
* MWP-76 Add sponsorship to support community (#83, #85)
* MWP-61 Changed project folder and files structure. (#69)
* MWP-67 Update issue templates and README (#75)
* MWP-68 Support for different languages (#77)
* MWP-72 Error: Library import requires a version (#73)
* MWP-27 Plugin freezes after canceling download (#78)
* Support of Cura 4.8.0+ (#60)
* TypeError: argument 1 has unexpected type 'NoneType' error fix (#66)
* Modify G-Code in Cura is ignored. No heat tower possible (#63)
* Save as TFT file extension fix (#64)
* Incorrect printer name on Monitor tab (#56)
* Bug with incorrectly displayed tooltips. (#52) 
* Bug with incorrectly displayed tooltips. (#51)
* Having problems to see printing times (#48)
* Remove files from repository, that should not exists in plugin. (#44)
* Cura periodically freezes if printer is turned off (#38)
* Cura freezes while MKS Plugin trying to reconnect to the printer (#36)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.1.2...1.2.0


## [1.1.2](https://github.com/PrintMakerLab/draft-repository/compare/1.0.2...1.1.2) - 2020

*Fixes from maker-base:*
* Added "disconnect" button
* Added "Fan" and "Motor" buttons
*  Jump to the monitoring page when the printer is connected
*  Modify multiple languages
*  SD card files cannot be queried during printing
*  Added the failure to transfer files, and only one file can be transferred at the same time.

*Fixes from the community:*
* Fixed button alignment (from PigeonFX)
* Make plugin compatible with multiple versions ( from adripo)
* Changed deprecated imports ( from adripo)
* Fixed image preview issue for FLSUN QQ-S (from peteristhegreat)
* Fixed generation and sending gcode  (from Elaugaste)

**Full Changelog**: https://github.com/Jeredian/mks-wifi-plugin/compare/1.0.2...1.1.2


## [1.0.2](https://github.com/PrintMakerLab/mks-wifi-plugin/releases/tag/1.0.2) - 2019

The first version of the plugin, that was uploaded to the Cura Marketplace