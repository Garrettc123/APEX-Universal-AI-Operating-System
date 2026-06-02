package com.apex.os.ui.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoGraph
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.apex.os.data.model.Overview
import com.apex.os.data.model.SystemRow
import com.apex.os.ui.theme.ApexAccentAmber
import com.apex.os.ui.theme.ApexAccentBlue
import com.apex.os.ui.theme.ApexAccentGreen
import com.apex.os.ui.theme.ApexBorder
import com.apex.os.ui.theme.ApexDanger
import com.apex.os.ui.theme.ApexSurface
import com.apex.os.ui.theme.ApexTextSecondary
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(viewModel: DashboardViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var showSettings by rememberSaveable { mutableStateOf(false) }

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
                        state.overview?.let {
                            Text(
                                "${it.state.uppercase(Locale.US)} · ${it.evolutionCycles} cycles · up ${formatUptime(it.uptimeSeconds)}",
                                style = MaterialTheme.typography.labelSmall,
                                color = ApexTextSecondary,
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                    }
                    IconButton(onClick = { showSettings = true }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings")
                    }
                },
            )
        },
    ) { padding ->
        when {
            state.loading -> CenteredLoader(padding)
            else -> DashboardContent(state, viewModel, padding)
        }
    }

    if (showSettings) {
        BackendUrlDialog(
            current = state.baseUrl,
            onDismiss = { showSettings = false },
            onSave = {
                viewModel.updateBaseUrl(it)
                showSettings = false
            },
        )
    }
}

@Composable
private fun CenteredLoader(padding: PaddingValues) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding),
        contentAlignment = Alignment.Center,
    ) {
        CircularProgressIndicator(color = ApexAccentGreen)
    }
}

@Composable
private fun DashboardContent(
    state: DashboardUiState,
    viewModel: DashboardViewModel,
    padding: PaddingValues,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(padding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        state.error?.let { item { ErrorBanner(it) } }

        state.overview?.let { ov ->
            item { KpiGrid(ov) }
            item { ActionBar(state, viewModel) }
        }

        item {
            Text(
                "SYSTEMS",
                style = MaterialTheme.typography.labelMedium,
                color = ApexTextSecondary,
                fontWeight = FontWeight.Bold,
            )
        }
        items(state.systems, key = { it.name }) { row -> SystemCard(row) }
    }
}

@Composable
private fun ErrorBanner(message: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = ApexDanger.copy(alpha = 0.12f)),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(
            message,
            color = ApexDanger,
            modifier = Modifier.padding(14.dp),
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun KpiGrid(ov: Overview) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            KpiCard(
                modifier = Modifier.weight(1f),
                label = "Intelligence",
                value = String.format(Locale.US, "%.4f", ov.intelligenceLevel),
                accent = ApexAccentBlue,
            )
            KpiCard(
                modifier = Modifier.weight(1f),
                label = "Healthy systems",
                value = "${ov.systemsHealthy}/${ov.systemsTotal}",
                accent = ApexAccentGreen,
            )
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            KpiCard(
                modifier = Modifier.weight(1f),
                label = "Total revenue",
                value = formatMoney(ov.totalRevenue),
                accent = ApexAccentGreen,
            )
            KpiCard(
                modifier = Modifier.weight(1f),
                label = "Annual projection",
                value = formatMoney(ov.annualProjection),
                accent = ApexAccentAmber,
            )
        }
    }
}

@Composable
private fun KpiCard(
    modifier: Modifier = Modifier,
    label: String,
    value: String,
    accent: Color,
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = ApexSurface),
        border = androidx.compose.foundation.BorderStroke(1.dp, ApexBorder),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(
                label.uppercase(Locale.US),
                style = MaterialTheme.typography.labelSmall,
                color = ApexTextSecondary,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                value,
                style = MaterialTheme.typography.headlineSmall,
                color = accent,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
            )
        }
    }
}

@Composable
private fun ActionBar(state: DashboardUiState, viewModel: DashboardViewModel) {
    val busy = state.actionInFlight != null
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            ActionButton(
                modifier = Modifier.weight(1f),
                label = "Evolve",
                icon = Icons.Filled.Bolt,
                enabled = !busy,
                container = ApexAccentGreen,
                onClick = viewModel::evolve,
            )
            ActionButton(
                modifier = Modifier.weight(1f),
                label = "Optimize",
                icon = Icons.Filled.Tune,
                enabled = !busy,
                container = ApexAccentBlue,
                onClick = viewModel::optimize,
            )
            ActionButton(
                modifier = Modifier.weight(1f),
                label = "Revenue",
                icon = Icons.Filled.AutoGraph,
                enabled = !busy,
                container = ApexAccentAmber,
                onClick = viewModel::runRevenueCycle,
            )
        }
        if (busy) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                CircularProgressIndicator(
                    modifier = Modifier.size(16.dp),
                    strokeWidth = 2.dp,
                    color = ApexAccentGreen,
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    "${state.actionInFlight}…",
                    style = MaterialTheme.typography.bodySmall,
                    color = ApexTextSecondary,
                )
            }
        }
    }
}

@Composable
private fun ActionButton(
    modifier: Modifier = Modifier,
    label: String,
    icon: ImageVector,
    enabled: Boolean,
    container: Color,
    onClick: () -> Unit,
) {
    Button(
        modifier = modifier,
        onClick = onClick,
        enabled = enabled,
        contentPadding = PaddingValues(vertical = 12.dp, horizontal = 4.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = container.copy(alpha = 0.18f),
            contentColor = container,
        ),
        shape = RoundedCornerShape(10.dp),
    ) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp))
        Spacer(Modifier.width(6.dp))
        Text(label, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun SystemCard(row: SystemRow) {
    val health = row.healthScore.toFloat().coerceIn(0f, 1f)
    val barColor = when {
        health >= 0.95f -> ApexAccentGreen
        health >= 0.85f -> ApexAccentAmber
        else -> ApexDanger
    }
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = ApexSurface),
        border = androidx.compose.foundation.BorderStroke(1.dp, ApexBorder),
    ) {
        Column(Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    row.name,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f),
                )
                Spacer(Modifier.width(8.dp))
                StatusDot(barColor, row.status)
            }
            Spacer(Modifier.height(8.dp))
            LinearProgressIndicator(
                progress = { health },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp),
                color = barColor,
                trackColor = ApexBorder,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                "health ${String.format(Locale.US, "%.1f%%", health * 100)}" +
                    (row.metrics["performance"]?.let { " · perf ${String.format(Locale.US, "%.1f%%", it)}" } ?: ""),
                style = MaterialTheme.typography.labelSmall,
                color = ApexTextSecondary,
                fontFamily = FontFamily.Monospace,
            )
        }
    }
}

@Composable
private fun StatusDot(color: Color, status: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .background(color, RoundedCornerShape(50)),
        )
        Spacer(Modifier.width(6.dp))
        Text(
            status.uppercase(Locale.US),
            style = MaterialTheme.typography.labelSmall,
            color = ApexTextSecondary,
        )
    }
}

@Composable
private fun BackendUrlDialog(
    current: String,
    onDismiss: () -> Unit,
    onSave: (String) -> Unit,
) {
    var text by remember { mutableStateOf(current) }
    androidx.compose.material3.AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = ApexSurface,
        title = { Text("Backend URL") },
        text = {
            Column {
                Text(
                    "Point the app at your APEX backend. Use http://10.0.2.2:8000/ for a server running on this machine via the emulator.",
                    style = MaterialTheme.typography.bodySmall,
                    color = ApexTextSecondary,
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = text,
                    onValueChange = { text = it },
                    singleLine = true,
                    label = { Text("https://your-backend/") },
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = { TextButton(onClick = { onSave(text) }) { Text("Save") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}

// -- formatting helpers -------------------------------------------------------

private fun formatMoney(value: Double): String = when {
    value >= 1_000_000_000 -> String.format(Locale.US, "$%.2fB", value / 1_000_000_000)
    value >= 1_000_000 -> String.format(Locale.US, "$%.2fM", value / 1_000_000)
    value >= 1_000 -> String.format(Locale.US, "$%.1fK", value / 1_000)
    else -> String.format(Locale.US, "$%.0f", value)
}

private fun formatUptime(seconds: Long): String {
    val h = seconds / 3600
    val m = (seconds % 3600) / 60
    return when {
        h > 0 -> "${h}h ${m}m"
        m > 0 -> "${m}m"
        else -> "${seconds}s"
    }
}
