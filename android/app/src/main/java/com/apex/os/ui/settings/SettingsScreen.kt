package com.apex.os.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.apex.os.ui.theme.ApexSurface
import com.apex.os.ui.theme.ApexTextSecondary

/**
 * Lets the user point the app at their own APEX backend. Persisted via
 * SettingsStore; saving re-loads every screen against the new URL.
 */
@Composable
fun SettingsScreen(
    currentBaseUrl: String,
    onSave: (String) -> Unit,
    contentPadding: PaddingValues,
) {
    var text by remember(currentBaseUrl) { mutableStateOf(currentBaseUrl) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(contentPadding)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Backend", style = MaterialTheme.typography.titleMedium)
        Card(colors = CardDefaults.cardColors(containerColor = ApexSurface)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    "Point APEX OS at your backend. For a server on this machine, use " +
                        "http://10.0.2.2:8000/ from the emulator, or your computer's LAN IP " +
                        "from a physical device.",
                    style = MaterialTheme.typography.bodySmall,
                    color = ApexTextSecondary,
                )
                OutlinedTextField(
                    value = text,
                    onValueChange = { text = it },
                    singleLine = true,
                    label = { Text("Base URL") },
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = { onSave(text) },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Save & reload")
                }
            }
        }
        Spacer(Modifier.height(4.dp))
        Text(
            "APEX OS · v1.0.0",
            style = MaterialTheme.typography.labelSmall,
            color = ApexTextSecondary,
        )
    }
}
