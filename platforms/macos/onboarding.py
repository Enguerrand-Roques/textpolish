"""First-launch window: the three things TextPolish needs (Ollama running, the
model downloaded, the Accessibility permission), each with one button, and a
progress bar for the 4.3 GB download. It checks every second, so a step turns
green as soon as it is done, even in another window (System Settings).

The checks and the download live in setup_check.py; this file is the window.
"""

from __future__ import annotations

import json
import os
import threading
import time

import objc
from AppKit import (
    NSApp,
    NSBackingStoreBuffered,
    NSColor,
    NSFloatingWindowLevel,
    NSMakeRect,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialSidebar,
    NSVisualEffectStateActive,
    NSVisualEffectView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskFullSizeContentView,
    NSWindowStyleMaskTitled,
    NSWorkspace,
)
from ApplicationServices import AXIsProcessTrusted
from Foundation import NSObject, NSURL
from WebKit import WKUserContentController, WKWebView, WKWebViewConfiguration

import i18n
import setup_check

_HTML_PATH = os.path.join(os.path.dirname(__file__), "onboarding.html")
_ACCESSIBILITY_URL = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
_OLLAMA_URL = "https://ollama.com/download"
_SIZE = (460, 380)


def needed() -> bool:
    """True if something is missing; fast enough to call at launch."""
    version = setup_check.ollama_version()
    return (version is None or not setup_check.version_ok(version)
            or bool(setup_check.missing_models()) or not AXIsProcessTrusted())


class _Bridge(NSObject):
    def userContentController_didReceiveScriptMessage_(self, controller, message):
        body = message.body()
        owner = self.owner
        owner.on_main(lambda: owner._handle(body))


class Onboarding(NSObject):
    """One per app. show() opens it; on_access_granted runs once the
    Accessibility permission appears (to install the shortcut)."""

    def initWithOnMain_shortcut_onAccessGranted_(self, on_main, shortcut, on_access_granted):
        self = objc.super(Onboarding, self).init()
        if self is None:
            return None
        self.on_main = on_main
        self._shortcut = shortcut
        self._on_access_granted = on_access_granted
        self._window = None
        self._ready = False
        self._pending: list[str] = []
        self._polling = False
        self._downloading = False
        self._download_error: str | None = None
        self._starting_ollama = False
        self._waiting_access = False
        self._had_access = AXIsProcessTrusted()
        return self

    # ── Window ──────────────────────────────────────────────────────────────

    @objc.python_method
    def _build(self):
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskFullSizeContentView
        w = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, *_SIZE), style, NSBackingStoreBuffered, False)
        w.setTitle_("TextPolish")
        w.setTitlebarAppearsTransparent_(True)
        w.setTitleVisibility_(1)  # hidden
        w.setMovableByWindowBackground_(True)
        w.setLevel_(NSFloatingWindowLevel)
        w.setReleasedWhenClosed_(False)
        w.setBackgroundColor_(NSColor.clearColor())
        w.setDelegate_(self)
        blur = NSVisualEffectView.alloc().initWithFrame_(w.contentView().bounds())
        blur.setMaterial_(NSVisualEffectMaterialSidebar)
        blur.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        blur.setState_(NSVisualEffectStateActive)
        blur.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        w.setContentView_(blur)

        config = WKWebViewConfiguration.alloc().init()
        controller = WKUserContentController.alloc().init()
        self._bridge = _Bridge.alloc().init()
        self._bridge.owner = self
        controller.addScriptMessageHandler_name_(self._bridge, "bridge")
        config.setUserContentController_(controller)
        self._webview = WKWebView.alloc().initWithFrame_configuration_(blur.bounds(), config)
        self._webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self._webview.setValue_forKey_(False, "drawsBackground")
        self._webview.setNavigationDelegate_(self)
        self._webview.loadFileURL_allowingReadAccessToURL_(
            NSURL.fileURLWithPath_(_HTML_PATH), NSURL.fileURLWithPath_(os.path.dirname(_HTML_PATH)))
        blur.addSubview_(self._webview)
        self._window = w

    def webView_didFinishNavigation_(self, webview, navigation):
        self._ready = True
        for code in self._pending:
            self._webview.evaluateJavaScript_completionHandler_(code, None)
        self._pending = []

    @objc.python_method
    def _js(self, code: str):
        if self._ready:
            self._webview.evaluateJavaScript_completionHandler_(code, None)
        else:
            self._pending.append(code)

    @objc.python_method
    def _call(self, fn: str, *args):
        self._js(f"App.{fn}({', '.join(json.dumps(a) for a in args)})")

    @objc.python_method
    def show(self):
        if self._window is None:
            self._build()
        self._call("setLanguage", i18n.LANG)
        self._window.center()
        self._window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        if not self._polling:
            self._polling = True
            threading.Thread(target=self._poll, daemon=True, name="onboarding-poll").start()

    def windowWillClose_(self, notification):
        self._polling = False  # a download in progress goes on

    # ── Checks, every second ────────────────────────────────────────────────

    @objc.python_method
    def _poll(self):
        while self._polling:
            state = self._check()
            self.on_main(lambda s=state: self._render(s))
            time.sleep(1.0)

    @objc.python_method
    def _check(self) -> dict:
        version = setup_check.ollama_version()
        if version is None and setup_check.ollama_installed() and not self._starting_ollama:
            self._starting_ollama = True
            threading.Thread(target=setup_check.start_ollama, daemon=True).start()
        ollama_ok = version is not None and setup_check.version_ok(version)
        missing = setup_check.missing_models() if ollama_ok else None
        return {
            "version": version,
            "installed": setup_check.ollama_installed(),
            "ollama_ok": ollama_ok,
            "missing": missing,
            "access": AXIsProcessTrusted(),
        }

    @objc.python_method
    def _render(self, s: dict):
        if s["ollama_ok"]:
            self._call("setStep", "ollama", "ok", "ollama_ok", None)
        elif s["version"]:
            self._call("setStep", "ollama", "todo", "ollama_old", "update", {"v": s["version"]})
        elif s["installed"]:
            self._call("setStep", "ollama", "busy", "ollama_starting", None)
        else:
            self._call("setStep", "ollama", "todo", "ollama_missing", "install")

        if not s["ollama_ok"]:
            self._call("setStep", "model", "wait", "model_wait", None)
        elif self._downloading:
            pass  # the download thread updates the bar
        elif self._download_error:
            self._call("setStep", "model", "error", self._download_error, "retry")
        elif s["missing"]:
            self._call("setStep", "model", "todo", "model_missing", "download")
        else:
            self._call("setStep", "model", "ok", "model_ok", None)

        if s["access"]:
            self._call("setStep", "access", "ok", "access_ok", None)
            if not self._had_access:
                self._had_access = True
                self._on_access_granted()
        elif self._waiting_access:
            self._call("setStep", "access", "busy", "access_waiting", None)
        else:
            self._call("setStep", "access", "todo", "access_missing", "open_settings")

        if s["ollama_ok"] and s["missing"] == [] and s["access"]:
            self._call("ready", self._shortcut)

    # ── Buttons ─────────────────────────────────────────────────────────────

    @objc.python_method
    def _handle(self, body: dict):
        if body.get("type") == "close":
            self._window.close()
        elif body.get("type") == "action":
            step = body.get("step")
            if step == "ollama":
                NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(_OLLAMA_URL))
            elif step == "model" and not self._downloading:
                self._download_error = None
                self._downloading = True
                self._call("setStep", "model", "busy", "", None)
                threading.Thread(target=self._download, daemon=True, name="model-pull").start()
            elif step == "access":
                self._waiting_access = True
                NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(_ACCESSIBILITY_URL))

    @objc.python_method
    def _download(self):
        def report(p: setup_check.Progress):
            left = p.seconds_left / 60 if p.seconds_left is not None else None
            self.on_main(lambda: self._call("setProgress", p.fraction, p.done / 1e9, p.total / 1e9, left))
        try:
            for model in setup_check.missing_models():
                setup_check.pull(model, report)
        except setup_check.PullError as e:
            self._download_error = str(e)
        finally:
            self._downloading = False
