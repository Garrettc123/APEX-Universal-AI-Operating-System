package com.apex.os.data

import android.content.Context
import com.apex.os.BuildConfig

/**
 * Tiny SharedPreferences-backed store for the backend base URL so the user
 * can point the app at their own deployed APEX backend from in-app Settings.
 */
class SettingsStore(context: Context) {

    private val prefs =
        context.getSharedPreferences("apex_settings", Context.MODE_PRIVATE)

    var baseUrl: String
        get() = prefs.getString(KEY_BASE_URL, BuildConfig.DEFAULT_BASE_URL)
            ?: BuildConfig.DEFAULT_BASE_URL
        set(value) {
            prefs.edit().putString(KEY_BASE_URL, normalize(value)).apply()
        }

    private fun normalize(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }

    companion object {
        private const val KEY_BASE_URL = "base_url"
    }
}
