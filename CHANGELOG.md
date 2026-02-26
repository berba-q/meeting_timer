# Changelog

# [](https://github.com/berba-q/meeting_timer/compare/v1.0.8...v) (2026-02-26)


### Features

* Implement automatic data cleanup feature ([b406dc9](https://github.com/berba-q/meeting_timer/commit/b406dc9e53cc2bd585378977e1dc2a0006cd1a97))



## [1.0.7](https://github.com/berba-q/meeting_timer/compare/v1.0.6...v1.0.7) (2026-02-25)


### Bug Fixes

* fixed an issue that caused app restarts ([87e4a2a](https://github.com/berba-q/meeting_timer/commit/87e4a2a595404fd403d65f874e710954275e408e))


### Features

* Added persistence and resume of timer when app crashes ([9f4bfd5](https://github.com/berba-q/meeting_timer/commit/9f4bfd55bbb5ca4fd5b474b58c511496abb58adf))
* Enhance meeting duration management including defining specific meeting end time which forces time redestribution from current part. ([440f266](https://github.com/berba-q/meeting_timer/commit/440f266ed1d6af0bfb591d0ea4080e3b73f64c26))



## [1.0.6](https://github.com/berba-q/meeting_timer/compare/v1.0.5...v1.0.6) (2026-01-27)


### Bug Fixes

* Fixed an issue where the weekend song editor hides behind the main application window on launch ([c03c815](https://github.com/berba-q/meeting_timer/commit/c03c815acc5284cb952923812890cd6e64de04be))
* Fixed an issue with light and dark mode themes not applying correctly on some devices ([edcd5f3](https://github.com/berba-q/meeting_timer/commit/edcd5f3e86fb136ca6e5122cc9ae665d98709c02))
* Fixed an issue with meeting parts parsing and a stray sting attached to meeting songs. ([89e0074](https://github.com/berba-q/meeting_timer/commit/89e0074a2cd8e426cd6784486ead5c6cf12ae12b))
* Fixed an issue with weekend meeting selection which was selecting watchtower in week + 1 instead of current week. ([ce440fa](https://github.com/berba-q/meeting_timer/commit/ce440fa6f0f9e03945945d0097d7d381ccf30b70))


### Features

* Add intellligent CO visit mode which adjust both midweek and weekend meetings with CO visit  meeting pattern ([190360b](https://github.com/berba-q/meeting_timer/commit/190360bc9f924857b61464d7994d43518db82f57))
* Implemented toast notification messages instead of system notifications to improve user experience. ([eeb2d71](https://github.com/berba-q/meeting_timer/commit/eeb2d71c70a45b505981551550b5a179c5b82fc0))



## [1.0.5](https://github.com/berba-q/meeting_timer/compare/v1.0.4...v1.0.5) (2025-07-03)


### Bug Fixes

* add SSL certificate dependency to requirements.txt ([cb7c41f](https://github.com/berba-q/meeting_timer/commit/cb7c41fc9403a25315759e5a105302194bb8a39e))
* adjust minimum font size for info labels to improve display stability ([80f7045](https://github.com/berba-q/meeting_timer/commit/80f7045d9cb821d3b6f3994a6336470a19375f44))
* correct download URLs in version.json to include 'v' prefix for version ([791db30](https://github.com/berba-q/meeting_timer/commit/791db3014e1dd5df74e7d15aebd87b4983c3668e))
* correct download URLs in version.json to include 'v' prefix for version ([041d3c8](https://github.com/berba-q/meeting_timer/commit/041d3c8964cb23744c869f7f0cf171268d782d92))
* correct signal disconnection for meeting countdown updates ([b090281](https://github.com/berba-q/meeting_timer/commit/b09028145adec2cf78a9ae0a3c242652752b8b6f))
* correct update check URL ([69eeacc](https://github.com/berba-q/meeting_timer/commit/69eeacc9951af07be9a892c96c6ee88d8a158156))
* correct variable reference for TAG_NAME in version.json generation ([09ef7bf](https://github.com/berba-q/meeting_timer/commit/09ef7bf31ffedddee45c353f9ab1f7fcdba83838))
* enhance current time update handling and prevent recursion in timer updates ([c30116c](https://github.com/berba-q/meeting_timer/commit/c30116c13f1ca593ed48fb014ea00152203ace3f))
* enhance localization for meeting song titles and comments ([1510d48](https://github.com/berba-q/meeting_timer/commit/1510d4833f0c1c1035321846687ba31fb3870ae6))
* enhance PyInstaller build commands to include additional dependencies ([55628b6](https://github.com/berba-q/meeting_timer/commit/55628b62f5716a01bb1e87d674281f7c658b80f3))
* enhance settings signal handling for meeting and reminder updates ([e0f7ea4](https://github.com/berba-q/meeting_timer/commit/e0f7ea4aa0a604608c5e3d0bd439aa5c55ce26c5))
* enhance timer state handling to reset reminders when stopped ([6a70b50](https://github.com/berba-q/meeting_timer/commit/6a70b5050a4a9921cf0fa033fa9fa8d50556ab58))
* enhance update check with error handling and silent mode ([354ef77](https://github.com/berba-q/meeting_timer/commit/354ef77a0cd6eb2a5600d62a89fab886260ceeb7))
* ensure meeting selection occurs before showing main window ([ab1789e](https://github.com/berba-q/meeting_timer/commit/ab1789e5b3381e8ca6c3b59b6c323f13ec589d94))
* fix issue with locale parsing for weekend songs ([3eab2f2](https://github.com/berba-q/meeting_timer/commit/3eab2f2676e5d90a14a41df75768b6e78a17a1e0))
* fixed a bug in chairman transition that prevented moving to the next part with the next button ([c7ab12a](https://github.com/berba-q/meeting_timer/commit/c7ab12ab3241e8ef3ef41680b25971e207a7acd3))
* fixed a bug that caused automatic update checks to fail ([6476f25](https://github.com/berba-q/meeting_timer/commit/6476f2511a3f79325e08b00a40f06a62431672c4))
* fixed the url ([5d46bc8](https://github.com/berba-q/meeting_timer/commit/5d46bc86374b688ea39a8dc67abc5abfe360ce96))
* implement SSL context for secure URL requests in update checker ([8f3673a](https://github.com/berba-q/meeting_timer/commit/8f3673abc629b36f2e3c1bd53e0afaa36c57a547))
* improve secondary display handling to update label and cleanup when disabled ([48b606b](https://github.com/berba-q/meeting_timer/commit/48b606b9fb9f072416bc62d04010d074f4e84a09))
* improve text formatting stability and reduce flickering in secondary display ([32ae04d](https://github.com/berba-q/meeting_timer/commit/32ae04dce5ee191a44eaa59999890b7fde684150))
* improve Watchtower issue retrieval logic for study periods ([50bbe59](https://github.com/berba-q/meeting_timer/commit/50bbe59020834ce25fd58c5746e52153c7f87b17))
* modify transition completion behavior to allow overtime instead of auto-advancing ([bd3c2a3](https://github.com/berba-q/meeting_timer/commit/bd3c2a362b3899207396b9f63019e317ac6a3eef))
* prevent recursion during secondary screen configuration updates ([4866b64](https://github.com/berba-q/meeting_timer/commit/4866b64bc179810589d116ce7197daa6c9a3df18))
* prevent recursion in settings and network display updates ([7dc4bed](https://github.com/berba-q/meeting_timer/commit/7dc4bed5f0e0eb7b9989badad4aac8860c148663))
* remove debug print statement for network display startup ([5402d2e](https://github.com/berba-q/meeting_timer/commit/5402d2efeef6d02df31ab67431825ed975c26207))
* replace hardcoded available languages with imported configuration ([d463d5e](https://github.com/berba-q/meeting_timer/commit/d463d5ed25329349960d126654678e6c038b2e8d))
* silently check for updates after a short delay in the main window ([f542e49](https://github.com/berba-q/meeting_timer/commit/f542e4914aa951b333a3cf061f623ddde59e7455))
* stop visual animations for buttons when stopping the meeting ([b06b568](https://github.com/berba-q/meeting_timer/commit/b06b5680ba04169b2ee30f1c140fcd25f51bb959))
* update download URLs and release notes in version.json ([acaca24](https://github.com/berba-q/meeting_timer/commit/acaca24ac4c7926db0a9f011b44ea69a74fc53ec))
* update font size and styling for timer display to enhance readability and prevent overflow ([fe0523e](https://github.com/berba-q/meeting_timer/commit/fe0523e49f7b8ed7af04396f3a8787a199192c33))
* update log message formatting in EPUBMeetingScraper ([85d28ec](https://github.com/berba-q/meeting_timer/commit/85d28ec9d8047484115cd535adedbc36df0ee7c0))
* update meeting cache generation to use EPUBMeetingScraper ([056037e](https://github.com/berba-q/meeting_timer/commit/056037ea47e0aa1339fa904a3c04f85eab6c312b))
* update PyInstaller commands to include translations data and adjust version handling in version.json ([d2ea3c4](https://github.com/berba-q/meeting_timer/commit/d2ea3c4dd41343412cf4aca5d86450af9c9cf770))
* update settings handling to show or hide secondary display based on configuration ([369af8e](https://github.com/berba-q/meeting_timer/commit/369af8ef09895fab70f0023a897f370d7892cf7e))
* update signal connection for current time and enhance secondary screen handling ([602aadd](https://github.com/berba-q/meeting_timer/commit/602aadd61131a5d9d6243b36ec27778904df82c8))
* update signal emissions for settings changes and add new signals for meeting and reminder settings ([11e9237](https://github.com/berba-q/meeting_timer/commit/11e9237efbdf6eea8c5a70d3b0ba2f18c5b7c38b))
* update user agent string and define available UI languages ([9969d67](https://github.com/berba-q/meeting_timer/commit/9969d679550c22b0687f65723666a8f93db7be5a))
* update version number to 1.0.4.1 ([1dff5a8](https://github.com/berba-q/meeting_timer/commit/1dff5a81eb4b09b368fa68149d4beaf437785928))
* **workflow:** enhance release notes generation with improved commit filtering and debugging output ([9360266](https://github.com/berba-q/meeting_timer/commit/9360266012a0f6d029fb55bdd1800157bb452364))


### Features

* add confirmation dialog for stopping a meeting ([e676fbb](https://github.com/berba-q/meeting_timer/commit/e676fbb0ff3c0124e95bfc0ce656d16259537bdf))
* add custom translation overrides for multiple languages ([c23d94d](https://github.com/berba-q/meeting_timer/commit/c23d94d6d0eed33f8990b27f26ad4c17859798f0))
* add language change handling to restart app with new language ([8bf192b](https://github.com/berba-q/meeting_timer/commit/8bf192b64203b83c12aeeec96ff919573545398c))
* Add language support for italian, french, german and spanish ([2b40d3d](https://github.com/berba-q/meeting_timer/commit/2b40d3d6a29b2f937f2e694cafaf26cecac653b3))
* add method to clear countdown message in central widget ([c3dc638](https://github.com/berba-q/meeting_timer/commit/c3dc638666a433d360392700a8fb5a9b8d0ebd4e))
* add reminder functionality for meeting start and next part with user-configurable settings ([1bb1c9f](https://github.com/berba-q/meeting_timer/commit/1bb1c9fdcad4de4f4c808b96622993a38ecde578))
* add translation loading and fallback mechanism ([f3767b3](https://github.com/berba-q/meeting_timer/commit/f3767b337a8d28948986cb8b32e22fa6d4fb6368))
* Add translation support for network status widget UI elements ([f3c3a59](https://github.com/berba-q/meeting_timer/commit/f3c3a59c6f6dab42d45f1e1520a9695cfc6d55af))
* add translation support for splash screen messages ([f09f6c5](https://github.com/berba-q/meeting_timer/commit/f09f6c58c8e0bcfd634b588db5c8dfc81a7115f1))
* enhance countdown message for upcoming meetings in network display ([47e8264](https://github.com/berba-q/meeting_timer/commit/47e82649ac5c019457a5912f3be354e0caa019d3))
* enhance countdown message localization for meeting start notifications ([e2b2510](https://github.com/berba-q/meeting_timer/commit/e2b2510c455de039ffda11b571200bc5d1cc1352))
* enhance date parsing with locale support and improved fallback methods ([1f0cb8f](https://github.com/berba-q/meeting_timer/commit/1f0cb8f4e310e025cc817026c0b88dcc972eaa89))
* enhance localization for "No meetings available" message in meeting selector ([f484ec5](https://github.com/berba-q/meeting_timer/commit/f484ec5d084dcfa1aa94274423647b44cdd88118))
* enhance localization for current meeting display in main window ([007708f](https://github.com/berba-q/meeting_timer/commit/007708fbb64c65394b941f2ac6ec8fd5f255de89))
* enhance localization for meeting starting soon message ([1155b91](https://github.com/berba-q/meeting_timer/commit/1155b91234e19e3af13dcf0608b90d3281e23153))
* enhance localization for meeting type display titles ([6840cdd](https://github.com/berba-q/meeting_timer/commit/6840cdd5321ea5e01fe4114688927671d29e3130))
* enhance localization for secondary display ([7dce535](https://github.com/berba-q/meeting_timer/commit/7dce535fe4b5fd22954c1ddcbfb166c90744e017))
* enhance localization for settings dialog and related components ([8e9847a](https://github.com/berba-q/meeting_timer/commit/8e9847a3c4e8b4f5e9a1dd94b955cb83276ecd18))
* enhance localization for weekend song editor dialog and descriptions ([ca84059](https://github.com/berba-q/meeting_timer/commit/ca840596cce71c205c58e31bf63ef08d6c08f19c))
* enhance localization in part editing and meeting management ([113c7df](https://github.com/berba-q/meeting_timer/commit/113c7df85b121a55b6ae20d75311b0a8c32118dd))
* enhance reminder functionality with improved timer management and visual cues ([c961457](https://github.com/berba-q/meeting_timer/commit/c9614575c68f167a27381962b6e86b4b1f9fc386))
* Enhance system tray notifications and improve icon handling ([3dc4e12](https://github.com/berba-q/meeting_timer/commit/3dc4e1224e2fe883dea5ebae683dc118d97b56d0))
* enhance timer controls with pause state management and visual feedback ([9e4b06e](https://github.com/berba-q/meeting_timer/commit/9e4b06e614348733920f23b2bd2bd0ff1d0c812d))
* enhance UI localization for meeting editor dialog ([0a35159](https://github.com/berba-q/meeting_timer/commit/0a35159856c88875efd0d0f1eaaf82821d90c2bb))
* enhanced meeting scraping with even faster response times ([92a4868](https://github.com/berba-q/meeting_timer/commit/92a486848adc3b3708a35f7a8970170bb0dc379a))
* implement localization for meeting parts ([4d41a05](https://github.com/berba-q/meeting_timer/commit/4d41a056f5f11e02a51d0d1b64d3c7114e0429a9))
* implement translation loading functionality ([5479d92](https://github.com/berba-q/meeting_timer/commit/5479d92e2215c450165c6f0623946608bba199e3))
* improve predicted end time calculation with real-time updates and safety checks ([5769957](https://github.com/berba-q/meeting_timer/commit/57699573c6f57285f47312cae86d193fda5ba91b))
* update central widget  to display current and next parts, clear countdown messages after meeting starts/ends ([ab42eb5](https://github.com/berba-q/meeting_timer/commit/ab42eb5af68dc3f3c9ab3a2737e44c10678f27fa))
* update localization for meeting controller ([402e4bf](https://github.com/berba-q/meeting_timer/commit/402e4bf64d9ecc4ec17e8412b34d86f70eab1858))
* update meeting selector behavior with blur effect during meeting start ([e6c2b8a](https://github.com/berba-q/meeting_timer/commit/e6c2b8a54d0459ded22bcac799435e70c3eec4eb))
* update overtime color coding for timer display ([c07cfe9](https://github.com/berba-q/meeting_timer/commit/c07cfe902f7970c7e44c2666dc90fce3714b58d2))
* version1.0 of scraper using api and scraping from epubs instead of wol.jw.org ([c394604](https://github.com/berba-q/meeting_timer/commit/c394604622f7345263f6b4ee252170683d3bc004))



## [1.0.2](https://github.com/berba-q/meeting_timer/compare/v1.0.1...v1.0.2) (2025-05-17)


### Bug Fixes

* add force secondary cleanup option and improve secondary display error handling ([d0bd77f](https://github.com/berba-q/meeting_timer/commit/d0bd77f33859e241e628609061c3263e20c98d1e))
* comment out unused language options in settings dialog ([aa08023](https://github.com/berba-q/meeting_timer/commit/aa080231a32e5d93e12550aa25bf26cf202b0c21))
* correct  chairman transition types for meeting types ([0846788](https://github.com/berba-q/meeting_timer/commit/0846788bb7967666676d69696ab7bc5bd619f986))
* ensure clean shutdown of secondary display and network display on close ([be2dc83](https://github.com/berba-q/meeting_timer/commit/be2dc835d0deeaa10e85e0b3c322090c28c267b7))
* ensure newline at end of file in requirements.txt and add platformdirs dependency ([7d819c0](https://github.com/berba-q/meeting_timer/commit/7d819c02497c72c087f22cb90f245083e7d9313b))
* Fixed a bug that caused the timer to flicker when timer is started ([b4550e0](https://github.com/berba-q/meeting_timer/commit/b4550e0472b2febcbe36ac672298dcc1336fdd6e))
* Fixed an issue with updating current meeting directly from work ([450b796](https://github.com/berba-q/meeting_timer/commit/450b7964632f26d6d3e04c14c3f36fc04df83908))
* **icons:** remove unused settings SVG icon ([1c392d9](https://github.com/berba-q/meeting_timer/commit/1c392d9137ee21a279874f5f11c00810ea3b3dcc))
* improve secondary display handling and error management in main window ([442d5de](https://github.com/berba-q/meeting_timer/commit/442d5de9882f1e77f10007d05385dbb2ffa9d5d7))
* improve update checking with retry logic and enhanced error handling ([5d6ebfd](https://github.com/berba-q/meeting_timer/commit/5d6ebfdbf1a4d39a373412f68c8aed8e1f234a7e))
* include release notes in version.json generation and adjust version parsing ([fd059b0](https://github.com/berba-q/meeting_timer/commit/fd059b09b260ee3035809f68a2773e515edabd44))
* **main_window:** update settings button label for clarity ([df04125](https://github.com/berba-q/meeting_timer/commit/df04125c6a48d047f41d56cce5b5a481e95795dc))
* **main_window:** update timer logic and UI improvements ([00ecea2](https://github.com/berba-q/meeting_timer/commit/00ecea21e1ad76c65122de9f7f9d4eb1b6f3caba))
* **network_display:** update font family for improved readability ([e49256e](https://github.com/berba-q/meeting_timer/commit/e49256e2f019f3898f522fb582e35c1b67f14ffd))
* return current meetings after attempting to load from local files ([1690621](https://github.com/berba-q/meeting_timer/commit/1690621de03b64ab9c39b3a81fcd74a43c58e40c))
* update cache directory handling to use platformdirs for better compatibility ([dd26e3d](https://github.com/berba-q/meeting_timer/commit/dd26e3d5321a1790429d269bbd637946c800e106))
* update cache TTL to 7 days and include week ID in cache file naming ([fdcffed](https://github.com/berba-q/meeting_timer/commit/fdcffed09519ed51f06a7f792889500638343217))
* **update_checker:** update CURRENT_VERSION to 1.0.2 and handle version string format ([1a1d227](https://github.com/berba-q/meeting_timer/commit/1a1d227a13a11b9ae5da817224b14c6d7eef2830))
* **version:** prepend 'v' to version number for consistency ([65b2faa](https://github.com/berba-q/meeting_timer/commit/65b2faa9cf84b6d0285cd6d9b0d08b53f483dfbc))
* **workflow:** add debug output for release-please and skip build if version not found ([b7e6bc5](https://github.com/berba-q/meeting_timer/commit/b7e6bc5ef9b45d2a42f64520f4b9ff683bee7c7b))
* **workflow:** correctly handle multiline release notes output ([93dd712](https://github.com/berba-q/meeting_timer/commit/93dd7124f58d8a5a6ecb1045c2f625809517956e))
* **workflow:** enable GitHub release and skip labeling in release-please action ([7750497](https://github.com/berba-q/meeting_timer/commit/77504972ce0e2d4477d419b8bd18a74458b9bab8))
* **workflow:** enhance changelog and release notes generation with commit hashes and structured output ([cf4ba47](https://github.com/berba-q/meeting_timer/commit/cf4ba47b801d523ba9e993e7fcdbf0b65c58b5a4))
* **workflow:** improve handling of multiline release notes in output ([363ee87](https://github.com/berba-q/meeting_timer/commit/363ee87d59a9e1bbf2b4748b12c45114e3e0d669))
* **workflow:** improve release notes generation by using a more reliable method to find previous tags and streamline commit logging ([f6e3223](https://github.com/berba-q/meeting_timer/commit/f6e3223bf703e9af0c44951f8701413133605a8c))
* **workflow:** restrict workflow trigger to main branch and remove version tag triggers ([e85b48f](https://github.com/berba-q/meeting_timer/commit/e85b48f40f8b182468deded542894e544c045c3e))
* **workflow:** simplify release notes handling and update output format ([258a26d](https://github.com/berba-q/meeting_timer/commit/258a26d4630204f9e2347e2d522cc01a38e53e71))
* **workflow:** update cache copy command for Windows and modify SHA256 generation command for macOS ([357e24f](https://github.com/berba-q/meeting_timer/commit/357e24fe2f509267f2c67c4baefa82fa9323570a))
* **workflow:** update CHANGELOG.md and version.json handling to use extracted version ([4e4e455](https://github.com/berba-q/meeting_timer/commit/4e4e455a06f5a2ac6d4b0a3a569d7898903fffb8))
* **workflow:** update release notes generation and improve GitHub token authentication for pushes ([6c7cda7](https://github.com/berba-q/meeting_timer/commit/6c7cda76a006d17e9f0bdefef8244da97e7dbea9))
* **workflow:** update release notes output format and improve AppStream metadata generation ([fe46123](https://github.com/berba-q/meeting_timer/commit/fe461231cfffda9aa5c0f4e218a1bad7c034f045))
* **workflow:** update release process to use actions for version extraction and GitHub release creation ([88dad1d](https://github.com/berba-q/meeting_timer/commit/88dad1d7b92d5ad608d5f60663051cee8aa95686))
* **workflow:** update upload-artifact action to version 3.1.2 for consistency ([31e8176](https://github.com/berba-q/meeting_timer/commit/31e817621d65c47936540f43f18b77acd37b0f7d))
* **workflow:** update upload-artifact and download-artifact actions to version 4 for improved functionality ([b4f9eb2](https://github.com/berba-q/meeting_timer/commit/b4f9eb2cbeac933b6d639d5b2bcb794d916d8446))


### Features

* add 'remember tools dock state' option and improve tools dock visibility handling ([cf21b57](https://github.com/berba-q/meeting_timer/commit/cf21b57ce99d8874dfc03832d18d1588c44ffac0))
* add placeholder for meeting view during loading in main window ([60074ad](https://github.com/berba-q/meeting_timer/commit/60074ad104abefd565cbe80e61244270b2773d71))
* add QMessageBox styling for dark and light themes with global font color overrides ([586e713](https://github.com/berba-q/meeting_timer/commit/586e71334933a8deb0f5c2a13a6719e30a282cb0))
* add SHA256 verification for downloaded updates in the update checker ([e7929c7](https://github.com/berba-q/meeting_timer/commit/e7929c70eb9b018b8667e97149d89c297fa831a5))
* add support for timer version tags and improve meeting cache generation in CI workflow ([9c979da](https://github.com/berba-q/meeting_timer/commit/9c979da7b7943375cf1e32b9b05823dcacbc5ad8))
* connect network display manager signals upon component availability ([6e810e0](https://github.com/berba-q/meeting_timer/commit/6e810e07ca07da5a34ebcbff64a9cec7527363df))
* enhance lazy loading with improved error handling and component dependency management ([ca7694d](https://github.com/berba-q/meeting_timer/commit/ca7694d6a012341f86a40ff33394dd14706a8291))
* enhance lazy loading with priority components and improved signaling ([ef20a41](https://github.com/berba-q/meeting_timer/commit/ef20a4176e09752180707901670186cd9934af15))
* enhance network display with improved HTML structure and dynamic timer updates ([20d8dfd](https://github.com/berba-q/meeting_timer/commit/20d8dfd35fa268ed936ca9f47b4640a816c15ee5))
* enhance network status synchronization and improve display management in main window ([833e03b](https://github.com/berba-q/meeting_timer/commit/833e03b5d76dcdc90ae0e956374bb5ba7981a677))
* enhance settings dialog with improved layout and QR code preview functionality ([dc24e56](https://github.com/berba-q/meeting_timer/commit/dc24e56b77e0cc0113ff5c9f86cf65485817a8f7))
* enhance weekend meeting song handling with custom dialog and automatic checks ([1c13daa](https://github.com/berba-q/meeting_timer/commit/1c13daa279db1d8fb70de92dbab98ddef30d9e84))
* implement caching for meeting URLs and HTML pages in the scraper to improve application startup performance ([4a4f276](https://github.com/berba-q/meeting_timer/commit/4a4f2762936cc4638d752eec740e267d0940f29f))
* implement lazy loading for components with improved UI responsiveness ([1aa8b0e](https://github.com/berba-q/meeting_timer/commit/1aa8b0ea24b3181aea6f3fa50f5a18e5674be5a7))
* implement lazy loading for components with pending action management ([e1599e5](https://github.com/berba-q/meeting_timer/commit/e1599e5f7790d9658a8f9b2ac209809c3586f620))
* implement state request handling and improve timer display updates in network components ([ce569f2](https://github.com/berba-q/meeting_timer/commit/ce569f2fe1645b0acc05351032bd440c971b8037))
* implemented lazy loading for UI components ([83ef338](https://github.com/berba-q/meeting_timer/commit/83ef33862ebd50708a4fad280521d9bea57d7b9a))
* improve secondary display management and settings synchronization ([d29bc8d](https://github.com/berba-q/meeting_timer/commit/d29bc8de18182b343855a7242a5c36c8a4280090))
* **release:** enhance release process with automatic generation and saving of release notes ([e06e03b](https://github.com/berba-q/meeting_timer/commit/e06e03b75f2c32c4f4a069568d9bea40b523a4b0))
* reorder UI component creation for improved layout and add progress bar placeholder ([d6bebe5](https://github.com/berba-q/meeting_timer/commit/d6bebe5cf9a9cd5610cc6c846148bb6a97177457))
* **workflow:** enhance release notes generation and update CHANGELOG.md process ([644efd3](https://github.com/berba-q/meeting_timer/commit/644efd301eff0c63d6c9aa06633b6437868b6bb8))
* **workflow:** update Node.js setup and improve release notes generation ([711786e](https://github.com/berba-q/meeting_timer/commit/711786e4f05d754384bafe28f839967d44c5255c))



## [1.0.1](https://github.com/berba-q/meeting_timer/compare/v1.0.0...v1.0.1) (2025-05-07)


### Bug Fixes

* Disable automatic update check on application startup ([dbafaa8](https://github.com/berba-q/meeting_timer/commit/dbafaa80ecb85f5bf02c06bf53ab2b9575d6a7fc))
* Fixed a bug affecting countdown ([d1d2677](https://github.com/berba-q/meeting_timer/commit/d1d2677899be1c4305f8d5592414ba3dc9719226))
* Fixed a bug that caused failures in saving secondary screen settings. ([4127f22](https://github.com/berba-q/meeting_timer/commit/4127f22adc04056aea10a04baa3fe418f2d515cb))
* Fixed an issue which caused countdown to show even when meeting is started ([2098a34](https://github.com/berba-q/meeting_timer/commit/2098a347902352cdb1c64137a7a9e46967ce1932))


### Features

* Enhance meeting editor and timer functionality with updated callbacks and duration adjustments ([f694d6d](https://github.com/berba-q/meeting_timer/commit/f694d6d3af36d6fef3cdc57914f982b11374530c))
* Implement countdown message and update timer display logic for pre-meeting state ([1369c25](https://github.com/berba-q/meeting_timer/commit/1369c25f568c895774bc9c4fe0493115844312ca))
* implement lazy loading for application components and add custom splash screen ([4c6695e](https://github.com/berba-q/meeting_timer/commit/4c6695ef5808f3852975e2c7a3bfd977e8a35d3d))
* Improve responsiveness of the main window and include docking tools ([75b0706](https://github.com/berba-q/meeting_timer/commit/75b0706255a155e1f4ba5682ca3fa6b94b025cae))
* timer display dynamically adjusts with screen size ([bcb3463](https://github.com/berba-q/meeting_timer/commit/bcb346314d407280fe4a64ff41b7d2f021aa3b21))



# 1.0.0 (2025-04-30)



