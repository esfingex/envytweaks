import St from 'gi://St';
import GObject from 'gi://GObject';
import Gio from 'gi://Gio';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

import * as Utility from '../lib/Utility.js';

const ICON_SIZE = 6;
const ICON_INTEL_FILE_NAME = '/img/intel_icon_plain.svg';
const ICON_NVIDIA_FILE_NAME = '/img/nvidia_icon_plain.svg';
const ICON_HYBRID_FILE_NAME = '/img/hybrid_icon_plain.svg';

export const TopBarView = GObject.registerClass(
class TopBarView extends PanelMenu.Button {
    _init(extensionObject) {
        super._init(0);
        this._all_settings = extensionObject.getSettings();
        this._extension_path = extensionObject.path;
        this._extension = extensionObject;
    }


    enable() {
        this.activeProfile = Utility.getCurrentProfile();
        this.chosenProfile = this.activeProfile === 'not_installed' ? 'not_installed' : this.activeProfile;
        this.restartPending = false;
        this.restart_menu_item = null;
        this.restart_menu_item_id = 0;

        this.icon_selector = new St.Icon({
            gicon : Gio.icon_new_for_string(this._extension_path + Utility.EXTENSION_ICON_FILE_NAME),
            style_class : 'system-status-icon',
            icon_size: ICON_SIZE
        });

        const _ = this._extension.gettext.bind(this._extension);

        this.integrated_menu_item = new PopupMenu.PopupMenuItem(_('Integrated'));
        this.integrated_menu_item_id = this.integrated_menu_item.connect('activate', () => {
            this._switchProfile('integrated');
        });

        this.hybrid_menu_item = new PopupMenu.PopupMenuItem(_('Hybrid'));
        this.hybrid_menu_item_id = this.hybrid_menu_item.connect('activate', () => {
            this._switchProfile('hybrid');
        });

        this.nvidia_menu_item = new PopupMenu.PopupMenuItem(_('Nvidia'));
        this.nvidia_menu_item_id = this.nvidia_menu_item.connect('activate', () => {
            this._switchProfile('nvidia');
        });

        this.separator_menu_item = new PopupMenu.PopupSeparatorMenuItem();
        this.menu.addMenuItem(this.separator_menu_item);
        this.menu.addMenuItem(this.integrated_menu_item);
        this.menu.addMenuItem(this.hybrid_menu_item);
        this.menu.addMenuItem(this.nvidia_menu_item);

        if (this.activeProfile === 'not_installed') {
            this.integrated_menu_item.sensitive = false;
            this.hybrid_menu_item.sensitive = false;
            this.nvidia_menu_item.sensitive = false;
            
            let warningItem = new PopupMenu.PopupMenuItem(_('envytweaks is not installed!'));
            warningItem.sensitive = false;
            this.menu.addMenuItem(warningItem, 0);
        }


        this._updateTopBarIcon();
    }

    _switchProfile(profile) {
        if (this.chosenProfile === profile || this.activeProfile === 'not_installed')
            return;

        const onComplete = (exitStatus) => {
            if (exitStatus === 126) {
                // User cancelled pkexec
                this._updateTopBarIcon();
                return;
            }
            if (exitStatus !== 0) {
                // Failure
                this._updateTopBarIcon();
                return;
            }

            // Success
            this.chosenProfile = profile;
            if (this.activeProfile === this.chosenProfile) {
                this.restartPending = false;
            } else {
                this.restartPending = true;
                Utility.requestReboot();
            }
            this._updateTopBarIcon();
        };

        if (profile === 'integrated') {
            Utility.switchIntegrated(onComplete);
        } else if (profile === 'hybrid') {
            Utility.switchHybrid(this._all_settings, onComplete);
        } else if (profile === 'nvidia') {
            Utility.switchNvidia(this._all_settings, onComplete);
        }
    }

    _updateTopBarIcon() {
        const profile = Utility.getCurrentProfile();
        
        // update chosenProfile if we are not in restartPending
        if (!this.restartPending) {
            this.chosenProfile = profile === 'not_installed' ? 'not_installed' : profile;
        }

        const profileConfig = {
            [Utility.GPU_PROFILE_INTEGRATED]: { icon: ICON_INTEL_FILE_NAME, menuItem: this.integrated_menu_item },
            [Utility.GPU_PROFILE_HYBRID]: { icon: ICON_HYBRID_FILE_NAME, menuItem: this.hybrid_menu_item },
            [Utility.GPU_PROFILE_NVIDIA]: { icon: ICON_NVIDIA_FILE_NAME, menuItem: this.nvidia_menu_item },
        };
        // Use chosenProfile for the icon check if restartPending, so it points to the target profile
        const targetProfile = this.restartPending ? this.chosenProfile : profile;
        const config = profileConfig[targetProfile];

        // Move selector icon to the active/chosen menu item
        const currentParent = this.icon_selector.get_parent();
        if (currentParent)
            currentParent.remove_child(this.icon_selector);
        if (config)
            config.menuItem.add_child(this.icon_selector);

        // Update top bar icon
        if (this.icon_top)
            this.remove_child(this.icon_top);
        
        const iconPath = this._extension_path + (config ? config.icon : Utility.EXTENSION_ICON_FILE_NAME);
        this.icon_top = new St.Icon({
            gicon: Gio.icon_new_for_string(iconPath),
            style_class: 'system-status-icon',
        });
        this.add_child(this.icon_top);

        // Update the restart required item in menu
        if (this.restartPending) {
            const _ = this._extension.gettext.bind(this._extension);
            if (!this.restart_menu_item) {
                this.restart_menu_item = new PopupMenu.PopupMenuItem(_('Restart Required*'));

                this.restart_menu_item_id = this.restart_menu_item.connect('activate', () => {
                    Utility.requestReboot();
                });
                this.menu.addMenuItem(this.restart_menu_item, 0);
            }
        } else {
            if (this.restart_menu_item) {
                this.restart_menu_item.disconnect(this.restart_menu_item_id);
                this.restart_menu_item.destroy();
                this.restart_menu_item = null;
                this.restart_menu_item_id = 0;
            }
        }
    }

    disable() {
        if (this.integrated_menu_item_id) {
            this.integrated_menu_item.disconnect(this.integrated_menu_item_id);
            this.integrated_menu_item_id = 0;
        }
        this.integrated_menu_item.destroy();
        this.integrated_menu_item = null;

        if (this.hybrid_menu_item_id) {
            this.hybrid_menu_item.disconnect(this.hybrid_menu_item_id);
            this.hybrid_menu_item_id = 0;
        }
        this.hybrid_menu_item.destroy();
        this.hybrid_menu_item = null;

        if (this.nvidia_menu_item_id) {
            this.nvidia_menu_item.disconnect(this.nvidia_menu_item_id);
            this.nvidia_menu_item_id = 0;
        }
        this.nvidia_menu_item.destroy();
        this.nvidia_menu_item = null;

        if (this.restart_menu_item) {
            this.restart_menu_item.disconnect(this.restart_menu_item_id);
            this.restart_menu_item.destroy();
            this.restart_menu_item = null;
            this.restart_menu_item_id = 0;
        }

        this.separator_menu_item.destroy();
        this.separator_menu_item = null;

        this.icon_selector = null;
    }
});
