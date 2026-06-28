package com.apex.os.ui.integrations

import androidx.compose.foundation.background
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
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.apex.os.data.model.Integration
import com.apex.os.ui.theme.ApexAccentGreen
import com.apex.os.ui.theme.ApexBorder
import com.apex.os.ui.theme.ApexSurface
import com.apex.os.ui.theme.ApexTextSecondary
import java.util.Locale

@Composable
fun IntegrationsScreen(viewModel: IntegrationsViewModel, contentPadding: PaddingValues) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    if (state.loading) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(contentPadding),
            contentAlignment = Alignment.Center,
        ) {
            CircularProgressIndicator(color = ApexAccentGreen)
        }
        return
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Text(
                "Everything you own, in one control plane",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
        }
        state.error?.let { msg ->
            item {
                Text(msg, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }
        }
        state.lastRunMessage?.let { msg ->
            item {
                Card(colors = CardDefaults.cardColors(containerColor = ApexAccentGreen.copy(alpha = 0.12f))) {
                    Text(
                        msg,
                        color = ApexAccentGreen,
                        modifier = Modifier.padding(12.dp),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }
        items(state.integrations, key = { it.id }) { integration ->
            IntegrationCard(
                integration = integration,
                triggering = state.triggeringId == integration.id,
                anyTriggering = state.triggeringId != null,
                onTrigger = { viewModel.trigger(integration) },
            )
        }
    }
}

@Composable
private fun IntegrationCard(
    integration: Integration,
    triggering: Boolean,
    anyTriggering: Boolean,
    onTrigger: () -> Unit,
) {
    val dotColor = if (integration.connected) ApexAccentGreen else ApexTextSecondary
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = ApexSurface),
        border = androidx.compose.foundation.BorderStroke(1.dp, ApexBorder),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Monogram badge.
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(dotColor.copy(alpha = 0.15f), RoundedCornerShape(10.dp)),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    integration.name.take(1).uppercase(Locale.US),
                    color = dotColor,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.titleMedium,
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(integration.name, fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyLarge)
                Text(
                    "${integration.category} · ${integration.automations} automations",
                    color = ApexTextSecondary,
                    style = MaterialTheme.typography.labelSmall,
                )
                StatusLine(integration.connected, dotColor, integration.status)
            }
            Spacer(Modifier.width(8.dp))
            if (triggering) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                    color = ApexAccentGreen,
                )
            } else {
                OutlinedButton(
                    onClick = onTrigger,
                    enabled = integration.connected && !anyTriggering,
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp),
                ) {
                    Icon(Icons.Filled.PlayArrow, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text("Run", style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }
}

@Composable
private fun StatusLine(connected: Boolean, color: Color, status: String) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 4.dp)) {
        Box(
            modifier = Modifier
                .size(7.dp)
                .background(color, RoundedCornerShape(50)),
        )
        Spacer(Modifier.width(6.dp))
        Text(
            if (connected) status.uppercase(Locale.US) else "TAP TO CONNECT",
            color = ApexTextSecondary,
            style = MaterialTheme.typography.labelSmall,
        )
    }
}
