package com.apex.os.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// GitHub-Mobile-inspired dark palette.
val ApexBackground = Color(0xFF0D1117)
val ApexSurface = Color(0xFF161B22)
val ApexSurfaceVariant = Color(0xFF21262D)
val ApexBorder = Color(0xFF30363D)
val ApexAccentGreen = Color(0xFF2EA043)
val ApexAccentBlue = Color(0xFF1F6FEB)
val ApexAccentAmber = Color(0xFFD29922)
val ApexDanger = Color(0xFFF85149)
val ApexTextPrimary = Color(0xFFE6EDF3)
val ApexTextSecondary = Color(0xFF8B949E)

private val ApexColorScheme = darkColorScheme(
    primary = ApexAccentGreen,
    onPrimary = Color(0xFF06140A),
    secondary = ApexAccentBlue,
    onSecondary = Color(0xFF06101F),
    background = ApexBackground,
    onBackground = ApexTextPrimary,
    surface = ApexSurface,
    onSurface = ApexTextPrimary,
    surfaceVariant = ApexSurfaceVariant,
    onSurfaceVariant = ApexTextSecondary,
    outline = ApexBorder,
    error = ApexDanger,
)

@Composable
fun ApexTheme(
    @Suppress("UNUSED_PARAMETER") darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    // The command dashboard is dark-only by design.
    MaterialTheme(
        colorScheme = ApexColorScheme,
        typography = Typography(),
        content = content,
    )
}
