import Gio from 'gi://Gio';
import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import GObject from 'gi://GObject';

import {ExtensionPreferences, gettext as _} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

export default class GpuProfileSwitcherPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        // Create a preferences page, with a single group
        const page = new Adw.PreferencesPage({
            title: _('General'),
            icon_name: 'dialog-information-symbolic',
        });
        
        const group = new Adw.PreferencesGroup({
            title: _('Settings'),
            description: _('Adjust extension and GPU profile switching options'),
        });

        const row_rtd3 = new Adw.SwitchRow({
            title: _('RTD3'),
            subtitle: _('Enable PCI-Express Runtime D3 (RTD3) Power Management on Hybrid mode. When not disabled, RTD3 allows the dGPU to be dynamically turned off when not in use'),
        });

        const row_rtd3_mode = new Adw.ComboRow({
            title: _('RTD3 Power Management Mode'),
            subtitle: _('Select the level of PCI-Express Runtime D3 Power Management (default is Coarse-Grained)'),
            model: Gtk.StringList.new([
                _('0: Disabled'),
                _('1: Fine-Grained'),
                _('2: Coarse-Grained (Default)'),
                _('3: Aggressive')
            ])
        });

        const row_force_composition_pipeline = new Adw.SwitchRow({
            title: _('Force Composition Pipeline'),
            subtitle: _('Enable ForceCompositionPipeline on Nvidia mode. Use this option if facing screen tearing'),
        });

        const row_coolbits = new Adw.SwitchRow({
            title: _('Coolbits'),
            subtitle: _('Enable Coolbits, which allows overclocking on Nvidia mode (not recommended)'),
        });

        const row_force_topbar_view = new Adw.SwitchRow({
            title: _('Force Topbar View'),
            subtitle: _('Show the GPU profile selector directly in the panel/topbar instead of the Quick Settings menu'),
        });
        
        row_rtd3.bind_property('active', row_rtd3_mode, 'sensitive', GObject.BindingFlags.DEFAULT);

        group.add(row_rtd3);
        group.add(row_rtd3_mode);
        group.add(row_force_composition_pipeline);
        group.add(row_coolbits);
        group.add(row_force_topbar_view);

        page.add(group);
        
        window._settings = this.getSettings();
        window._settings.bind('rtd3', row_rtd3, 'active', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('rtd3-mode', row_rtd3_mode, 'selected', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('force-composition-pipeline', row_force_composition_pipeline, 'active', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('coolbits', row_coolbits, 'active', Gio.SettingsBindFlags.DEFAULT);
        window._settings.bind('force-topbar-view', row_force_topbar_view, 'active', Gio.SettingsBindFlags.DEFAULT);
        window.add(page);
    }
}
