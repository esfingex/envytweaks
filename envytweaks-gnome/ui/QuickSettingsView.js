import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import GObject from 'gi://GObject';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as QuickSettings from 'resource:///org/gnome/shell/ui/quickSettings.js';

import * as Utility from '../lib/Utility.js';

export const QuickSettingsToggle = GObject.registerClass(
class QuickSettingsToggle extends QuickSettings.QuickMenuToggle {  
    _init(extensionObject) {
        this.activeProfile = Utility.getCurrentProfile(); // initialized profile since startup
        
        if (this.activeProfile === Utility.GPU_PROFILE_NOT_INSTALLED) {
            this.chosenProfile = 'not_installed';
        } else if (this.activeProfile === Utility.GPU_PROFILE_UNKNOWN) {
            this.chosenProfile = 'unknown';
        } else {
            this.chosenProfile = this.activeProfile;
        }
        
        this.restartPending = false;
        this.doNotSwitch = false;
        
        super._init({
            title: 'GPU Profile',
            subtitle: this.chosenProfile === 'not_installed' ? 'Not Installed' : Utility.capitalizeFirstLetter(this.chosenProfile),
            iconName: 'power-profile-performance-symbolic',
            toggleMode: false, // disable the possibility to click the button
            checked: this.activeProfile === 'hybrid' || this.activeProfile === 'nvidia',
        });
        this._all_settings = extensionObject.getSettings();

        // This function is unique to this class. It adds a nice header with an icon, title and optional subtitle.
        if (this.activeProfile === Utility.GPU_PROFILE_NOT_INSTALLED) {
            this.menu.setHeader('dialog-warning-symbolic', super.title, 'envytweaks is not installed!');
        } else {
            this.menu.setHeader('power-profile-performance-symbolic', super.title, 'Choose a GPU mode');
        }

        // add a sections of items to the menu
        this._itemsSection = new PopupMenu.PopupMenuSection();
        
        this._integratedAction = this._itemsSection.addAction('Integrated' + (this.activeProfile === 'integrated' ? ' (Active)' : ''), () => {
            if (this.chosenProfile !== 'integrated' && !this.doNotSwitch) {
                this.doNotSwitch = true;
                super.subtitle = 'Switching...';
                this.menu.setHeader('power-profile-performance-symbolic', super.title, 'Switching to Integrated mode...');
                Utility.switchIntegrated(this._onSwitchComplete.bind(this));
            }
        });
        
        this._hybridAction = this._itemsSection.addAction('Hybrid' + (this.activeProfile === 'hybrid' ? ' (Active)' : ''), () => {
            if (this.chosenProfile !== 'hybrid' && !this.doNotSwitch) {
                this.doNotSwitch = true;
                super.subtitle = 'Switching...';
                this.menu.setHeader('power-profile-performance-symbolic', super.title, 'Switching to Hybrid mode...');
                Utility.switchHybrid(this._all_settings, this._onSwitchComplete.bind(this));
            }
        });
        
        this._nvidiaAction = this._itemsSection.addAction('Nvidia'+ (this.activeProfile === 'nvidia' ? ' (Active)' : ''), () => {
            if (this.chosenProfile !== 'nvidia' && !this.doNotSwitch) {
                this.doNotSwitch = true;
                super.subtitle = 'Switching...';
                this.menu.setHeader('power-profile-performance-symbolic', super.title, 'Switching to Nvidia mode...');
                Utility.switchNvidia(this._all_settings, this._onSwitchComplete.bind(this));
            }
        });

        if (this.activeProfile === Utility.GPU_PROFILE_NOT_INSTALLED) {
            this._integratedAction.sensitive = false;
            this._hybridAction.sensitive = false;
            this._nvidiaAction.sensitive = false;
        }

        this.menu.addMenuItem(this._itemsSection);

        // Add an entry-point for more settings
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        const settingsItem = this.menu.addAction(
            'More Settings',
            () => extensionObject.openPreferences()
        );

        // Ensure the settings are unavailable when the screen is locked
        settingsItem.visible = Main.sessionMode.allowSettings;
        this.menu._settingsActions[extensionObject.uuid] = settingsItem;
    }

    _onSwitchComplete(exitStatus) {
        if (exitStatus === 126) {
            // User cancelled authorization
            this.chosenProfile = Utility.getCurrentProfile();
            if (this.restartPending) {
                super.subtitle = Utility.capitalizeFirstLetter(this.chosenProfile) + '*';
                this.menu.setHeader('power-profile-performance-symbolic', super.title, 
                    'Restart to apply ' + Utility.capitalizeFirstLetter(this.chosenProfile) + ' mode');
            } else {
                super.subtitle = Utility.capitalizeFirstLetter(this.chosenProfile);
                this.menu.setHeader('power-profile-performance-symbolic', super.title, 'Choose a GPU mode');
            }
            this.doNotSwitch = false;
            return;
        }

        if (exitStatus !== 0) {
            // Error occurred
            this.chosenProfile = Utility.getCurrentProfile();
            super.subtitle = 'Error';
            this.menu.setHeader('dialog-warning-symbolic', super.title, 'Switching failed (code ' + exitStatus + ')');
            this.doNotSwitch = false;
            return;
        }

        // Success
        let priorProfile = this.chosenProfile;
        this.chosenProfile = Utility.getCurrentProfile();

        if (this.activeProfile === this.chosenProfile) {
            super.subtitle = Utility.capitalizeFirstLetter(this.activeProfile);
            this.menu.setHeader('power-profile-performance-symbolic', super.title, 'Choose a GPU mode');
            this.restartPending = false;
        } else {
            super.subtitle = Utility.capitalizeFirstLetter(this.chosenProfile) + '*';
            this.menu.setHeader('power-profile-performance-symbolic', super.title, 
                'Restart to apply ' + Utility.capitalizeFirstLetter(this.chosenProfile) + ' mode');
            Utility.requestReboot();
            this.restartPending = true;
        }
        
        this.doNotSwitch = false;
    }
});

export const QuickSettingsIndicator = GObject.registerClass(
class QuickSettingsIndicator extends QuickSettings.SystemIndicator {
    _init(extensionObject) {
        super._init();
    }

    enable() {
        this._indicator = this._addIndicator();
        this._indicator.icon_name = 'power-profile-performance-symbolic';
        this._indicator.visible = false;
    }

    disable() {
        this.quickSettingsItems.forEach(item => item.destroy());
        this._indicator.destroy();
        super.destroy();
    }
});
