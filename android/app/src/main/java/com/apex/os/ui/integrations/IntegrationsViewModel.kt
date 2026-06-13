package com.apex.os.ui.integrations

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.apex.os.data.ApexRepository
import com.apex.os.data.SettingsStore
import com.apex.os.data.model.Integration
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class IntegrationsUiState(
    val loading: Boolean = false,
    val integrations: List<Integration> = emptyList(),
    val triggeringId: String? = null,
    val lastRunMessage: String? = null,
    val error: String? = null,
)

class IntegrationsViewModel(
    private val repository: ApexRepository,
    private val settings: SettingsStore,
) : ViewModel() {

    private val _state = MutableStateFlow(IntegrationsUiState(loading = true))
    val state: StateFlow<IntegrationsUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(loading = it.integrations.isEmpty(), error = null) }
            runCatching { repository.integrations() }
                .onSuccess { list ->
                    _state.update { it.copy(loading = false, integrations = list, error = null) }
                }
                .onFailure { t ->
                    _state.update { it.copy(loading = false, error = friendly(t)) }
                }
        }
    }

    fun trigger(integration: Integration) {
        if (_state.value.triggeringId != null) return
        viewModelScope.launch {
            _state.update { it.copy(triggeringId = integration.id, lastRunMessage = null, error = null) }
            runCatching { repository.triggerIntegration(integration.id) }
                .onSuccess { run ->
                    _state.update {
                        it.copy(triggeringId = null, lastRunMessage = "${run.status.uppercase()} · ${run.detail}")
                    }
                    refresh()
                }
                .onFailure { t ->
                    _state.update { it.copy(triggeringId = null, error = friendly(t)) }
                }
        }
    }

    fun clearMessage() = _state.update { it.copy(lastRunMessage = null) }

    private fun friendly(t: Throwable): String {
        val reason = t.message ?: t.javaClass.simpleName
        return "Couldn't reach APEX backend (${settings.baseUrl}). $reason"
    }

    class Factory(
        private val repository: ApexRepository,
        private val settings: SettingsStore,
    ) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return IntegrationsViewModel(repository, settings) as T
        }
    }
}
