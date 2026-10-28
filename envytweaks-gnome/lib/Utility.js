import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import * as SystemActions from 'resource:///org/gnome/shell/misc/systemActions.js';

export const EXTENSION_ICON_FILE_NAME = '/img/icon.png';

export const GPU_PROFILE_INTEGRATED = "integrated";
export const GPU_PROFILE_HYBRID = "hybrid";
export const GPU_PROFILE_NVIDIA = "nvidia";
export const GPU_PROFILE_UNKNOWN = "unknown";
export const GPU_PROFILE_NOT_INSTALLED = "not_installed";

export function getEnvytweaksPath() {
    return GLib.find_program_in_path("envytweaks");
}

export function getCurrentProfile() {
    const envytweaksPath = getEnvytweaksPath();
    if (!envytweaksPath) {
        return GPU_PROFILE_NOT_INSTALLED;
    }

    try {
        let proc = new Gio.Subprocess({
            argv: [envytweaksPath, '--query'],
            flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE,
        });
        proc.init(null);
        let [ok, stdout] = proc.communicate_utf8(null, null);

        if (ok && stdout) {
            const profileString = stdout.trim().toLowerCase();

            if (profileString === GPU_PROFILE_INTEGRATED ||
                profileString === GPU_PROFILE_HYBRID ||
                profileString === GPU_PROFILE_NVIDIA) {
                return profileString;
            }
        }

        return GPU_PROFILE_UNKNOWN;
    } catch (e) {
        return GPU_PROFILE_UNKNOWN;
    }
}


export function capitalizeFirstLetter(string) {
    if (!string) return "";
    return string.charAt(0).toUpperCase() + string.slice(1);
}

export function switchIntegrated(onComplete = null) {
    _execSwitch(GPU_PROFILE_INTEGRATED, [], onComplete);
}

export function switchHybrid(all_settings, onComplete = null) {
    const args = [];
    if (all_settings.get_boolean("rtd3")) {
        const rtd3Mode = all_settings.get_int("rtd3-mode");
        args.push('--rtd3', String(rtd3Mode));
    }
    _execSwitch(GPU_PROFILE_HYBRID, args, onComplete);
}

export function switchNvidia(all_settings, onComplete = null) {
    const args = [];
    if (all_settings.get_boolean("force-composition-pipeline")) {
        args.push('--force-comp');
    }
    if (all_settings.get_boolean("coolbits")) {
        args.push('--coolbits');
    }
    _execSwitch(GPU_PROFILE_NVIDIA, args, onComplete);
}

export function requestReboot() {
    let systemActions = SystemActions.getDefault();
    systemActions.activateRestart();
}

function _execSwitch(profile, args, onComplete) {
    const envytweaksPath = getEnvytweaksPath();
    const pkexecPath = GLib.find_program_in_path("pkexec");

    if (!envytweaksPath || !pkexecPath) {
        if (typeof onComplete === 'function') {
            onComplete(127);
        }
        return;
    }

    try {
        let proc = Gio.Subprocess.new(
            [pkexecPath, envytweaksPath, '-s', profile, ...args],
            Gio.SubprocessFlags.NONE
        );

        proc.wait_async(null, (obj, res) => {
            try {
                obj.wait_finish(res);
                let exitStatus = 0;
                if (obj.get_if_exited()) {
                    exitStatus = obj.get_exit_status();
                } else {
                    exitStatus = -1;
                }
                if (typeof onComplete === 'function') {
                    onComplete(exitStatus);
                }
            } catch (e) {
                if (typeof onComplete === 'function') {
                    onComplete(-1);
                }
            }
        });
    } catch (e) {
        if (typeof onComplete === 'function') {
            onComplete(-1);
        }
    }
}
