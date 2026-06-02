package com.apex.os

import android.app.Application
import com.apex.os.data.ApexRepository
import com.apex.os.data.SettingsStore

/**
 * App entry point. Holds the process-wide singletons (settings + repository)
 * so we avoid a DI framework for a single-screen app while keeping the
 * wiring in one obvious place.
 */
class ApexApplication : Application() {

    lateinit var settings: SettingsStore
        private set

    lateinit var repository: ApexRepository
        private set

    override fun onCreate() {
        super.onCreate()
        settings = SettingsStore(this)
        repository = ApexRepository(settings)
    }
}
