package com.apex.os

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.apex.os.ui.AppShell
import com.apex.os.ui.dashboard.DashboardViewModel
import com.apex.os.ui.integrations.IntegrationsViewModel
import com.apex.os.ui.theme.ApexTheme

class MainActivity : ComponentActivity() {

    private val dashboardViewModel: DashboardViewModel by viewModels {
        val app = application as ApexApplication
        DashboardViewModel.Factory(app.repository, app.settings)
    }

    private val integrationsViewModel: IntegrationsViewModel by viewModels {
        val app = application as ApexApplication
        IntegrationsViewModel.Factory(app.repository, app.settings)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            ApexTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AppShell(dashboardViewModel, integrationsViewModel)
                }
            }
        }
    }
}
