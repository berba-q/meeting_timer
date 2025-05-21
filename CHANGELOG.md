# Changelog

# [](https://github.com/berba-q/meeting_timer/compare/v1.0.3...v) (2025-05-21)


### Bug Fixes

* add SSL certificate dependency to requirements.txt ([cb7c41f](https://github.com/berba-q/meeting_timer/commit/cb7c41fc9403a25315759e5a105302194bb8a39e))
* correct download URLs in version.json to include 'v' prefix for version ([041d3c8](https://github.com/berba-q/meeting_timer/commit/041d3c8964cb23744c869f7f0cf171268d782d92))
* implement SSL context for secure URL requests in update checker ([8f3673a](https://github.com/berba-q/meeting_timer/commit/8f3673abc629b36f2e3c1bd53e0afaa36c57a547))
* **workflow:** enhance release notes generation with improved commit filtering and debugging output ([9360266](https://github.com/berba-q/meeting_timer/commit/9360266012a0f6d029fb55bdd1800157bb452364))


### Features

* add confirmation dialog for stopping a meeting ([e676fbb](https://github.com/berba-q/meeting_timer/commit/e676fbb0ff3c0124e95bfc0ce656d16259537bdf))
* add reminder functionality for meeting start and next part with user-configurable settings ([1bb1c9f](https://github.com/berba-q/meeting_timer/commit/1bb1c9fdcad4de4f4c808b96622993a38ecde578))
* enhance reminder functionality with improved timer management and visual cues ([c961457](https://github.com/berba-q/meeting_timer/commit/c9614575c68f167a27381962b6e86b4b1f9fc386))
* enhance timer controls with pause state management and visual feedback ([9e4b06e](https://github.com/berba-q/meeting_timer/commit/9e4b06e614348733920f23b2bd2bd0ff1d0c812d))
* update meeting selector behavior with blur effect during meeting start ([e6c2b8a](https://github.com/berba-q/meeting_timer/commit/e6c2b8a54d0459ded22bcac799435e70c3eec4eb))



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



