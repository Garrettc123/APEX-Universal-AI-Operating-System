package com.apex.os.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.Hub
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.apex.os.ui.dashboard.DashboardScreen
import com.apex.os.ui.dashboard.DashboardViewModel
import com.apex.os.ui.integrations.IntegrationsScreen
import com.apex.os.ui.integrations.IntegrationsViewModel
import com.apex.os.ui.settings.SettingsScreen
import com.apex.os.ui.theme.ApexAccentGreen
import com.apex.os.ui.theme.ApexSurface
import com.apex.os.ui.theme.ApexTextSecondary

private enum class Tab(val label: String, val icon: ImageVector) {
    DASHBOARD("Command", Icons.Filled.Dashboard),
    INTEGRATIONS("Integrations", Icons.Filled.Hub),
    SETTINGS("Settings", Icons.Filled.Settings),
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppShell(
    dashboardViewModel: DashboardViewModel,
    integrationsViewModel: IntegrationsViewModel,
) {
    var tab by rememberSaveable { mutableStateOf(Tab.DASHBOARD) }
    val dashboardState by dashboardViewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = MaterialTheme.colorScheme.onBackground,
                ),
                title = {
                    Column {
                        Text("APEX OS", fontWeight = FontWeight.Bold)
                        Text(
                            tab.label,
                            style = MaterialTheme.typography.labelSmall,
                            color = ApexTextSecondary,
                        )
                    }
                },
                actions = {
                    if (tab != Tab.SETTINGS) {
                        IconButton(
                            onClick = {
                                when (tab) {
                                    Tab.DASHBOARD -> dashboardViewModel.refresh()
                                    Tab.INTEGRATIONS -> integrationsViewModel.refresh()
                                    Tab.SETTINGS -> Unit
                                }
                            },
                        ) {
                            Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                        }
                    }
                },
            )
        },
        bottomBar = {
            NavigationBar(containerColor = ApexSurface) {
                Tab.entries.forEach { entry ->
                    NavigationBarItem(
                        selected = tab == entry,
                        onClick = { tab = entry },
                        icon = { Icon(entry.icon, contentDescription = entry.label) },
                        label = { Text(entry.label) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = ApexAccentGreen,
                            selectedTextColor = ApexAccentGreen,
                            indicatorColor = ApexAccentGreen.copy(alpha = 0.15f),
                            unselectedIconColor = ApexTextSecondary,
                            unselectedTextColor = ApexTextSecondary,
                        ),
                    )
                }
            }
        },
    ) { padding ->
        when (tab) {
            Tab.DASHBOARD -> DashboardScreen(dashboardViewModel, padding)
            Tab.INTEGRATIONS -> IntegrationsScreen(integrationsViewModel, padding)
            Tab.SETTINGS -> SettingsScreen(
                currentBaseUrl = dashboardState.baseUrl,
                onSave = { url ->
                    dashboardViewModel.updateBaseUrl(url)
                    integrationsViewModel.refresh()
                    tab = Tab.DASHBOARD
                },
                contentPadding = padding,
            )
        }
    }
}
