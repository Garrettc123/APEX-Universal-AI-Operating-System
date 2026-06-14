package com.apex.os.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.apex.os.data.ApexRepository
import com.apex.os.data.SettingsStore
import com.apex.os.data.model.Overview
import com.apex.os.data.model.Revenue
import com.apex.os.data.model.SystemRow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Immutable UI state rendered by [DashboardScreen]. */
data class DashboardUiState(
    val loading: Boolean = false,
    val refreshing: Boolean = false,
    val actionInFlight: String? = null,
    val overview: Overview? = null,
    val systems: List<SystemRow> = emptyList(),
    val revenue: Revenue? = null,
    val error: String? = null,
    val baseUrl: String = "",
)

class DashboardViewModel(
    private val repository: ApexRepository,
    private val settings: SettingsStore,
) : ViewModel() {

    private val _state = MutableStateFlow(DashboardUiState(loading = true, baseUrl = settings.baseUrl))
    val state: StateFlow<DashboardUiState> = _state.asStateFlow()

    init {
        refresh(initial = true)
    }

    /** Pull a fresh snapshot of every screen section. */
    fun refresh(initial: Boolean = false) {
        viewModelScope.launch {
            _state.update {
                it.copy(
                    loading = initial,
                    refreshing = !initial,
                    error = null,
                    baseUrl = settings.baseUrl,
                )
            }
            runCatching {
                val overview = repository.overview()
                val systems = repository.systems()
                val revenue = repository.revenue()
                Triple(overview, systems, revenue)
            }.onSuccess { (overview, systems, revenue) ->
                _state.update {
                    it.copy(
                        loading = false,
                        refreshing = false,
                        overview = overview,
                        systems = systems,
                        revenue = revenue,
                        error = null,
                    )
                }
            }.onFailure { t ->
                _state.update {
                    it.copy(
                        loading = false,
                        refreshing = false,
                        error = friendly(t),
                    )
                }
            }
        }
    }

    fun evolve() = runAction("Evolving") { repository.evolve() }

    fun optimize() = runAction("Optimizing") { repository.optimize() }

    fun runRevenueCycle() = runAction("Generating revenue") { repository.runRevenueCycle() }

    /** Persist a new backend URL and reload against it. */
    fun updateBaseUrl(url: String) {
        if (url.isBlank()) return
        settings.baseUrl = url
        refresh(initial = true)
    }

    private fun runAction(label: String, block: suspend () -> Any) {
        if (_state.value.actionInFlight != null) return
        viewModelScope.launch {
            _state.update { it.copy(actionInFlight = label, error = null) }
            runCatching { block() }
                .onFailure { t -> _state.update { it.copy(error = friendly(t)) } }
            _state.update { it.copy(actionInFlight = null) }
            // Re-pull everything so all cards reflect the cycle's side effects.
            refresh()
        }
    }

    private fun friendly(t: Throwable): String {
        val reason = t.message ?: t.javaClass.simpleName
        return "Couldn't reach APEX backend (${settings.baseUrl}). $reason"
    }

    /** Factory so we can inject the app-scoped repository/settings. */
    class Factory(
        private val repository: ApexRepository,
        private val settings: SettingsStore,
    ) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return DashboardViewModel(repository, settings) as T
        }
    }
}
