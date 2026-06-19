#!/bin/bash
# Shared Functions for Channel Director Automation Scripts
# Source this file after sourcing config.sh

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date "+${LOG_FORMAT}")
    
    case "$level" in
        INFO)
            echo "${timestamp} [INFO] ${message}"
            ;;
        DEBUG)
            if [[ "$LOG_LEVEL" == "DEBUG" ]]; then
                echo "${timestamp} [DEBUG] ${message}"
            fi
            ;;
        WARN)
            echo "${timestamp} [WARN] ${message}" >&2
            ;;
        ERROR)
            echo "${timestamp} [ERROR] ${message}" >&2
            ;;
    esac
}

info() { log INFO "$@"; }
debug() { log DEBUG "$@"; }
warn() { log WARN "$@"; }
error() { log ERROR "$@"; }

fatal() {
    error "$@"
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════
# DIRECTORY INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

ensure_directories() {
    local dirs=(
        "$WEEKLY_DIR"
        "$MONTHLY_DIR"
        "$QBR_DIR"
        "$LOGS_DIR"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir" || fatal "Failed to create directory: $dir"
            info "Created directory: $dir"
        fi
    done
}

# ═══════════════════════════════════════════════════════════════════════════
# CLI COMMAND EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

run_cli() {
    local cmd="$@"
    
    debug "Executing CLI: $cmd"
    
    # Activate venv, run command, deactivate
    (
        source "${VENV_PATH}/bin/activate" || fatal "Failed to activate venv"
        eval "$CLI_CMD $cmd" || return 1
        deactivate
    ) || return 1
    
    return 0
}

run_cli_json() {
    local cmd="$@"
    run_cli "$cmd --json" || return 1
}

# ═══════════════════════════════════════════════════════════════════════════
# FILE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

save_json_file() {
    local filename="$1"
    local content="$2"
    
    if [[ -z "$filename" ]] || [[ -z "$content" ]]; then
        error "save_json_file: missing filename or content"
        return 1
    fi
    
    echo "$content" > "$filename" || fatal "Failed to save file: $filename"
    debug "Saved JSON file: $filename"
}

save_text_file() {
    local filename="$1"
    local content="$2"
    
    if [[ -z "$filename" ]] || [[ -z "$content" ]]; then
        error "save_text_file: missing filename or content"
        return 1
    fi
    
    echo "$content" > "$filename" || fatal "Failed to save file: $filename"
    debug "Saved text file: $filename"
}

# ═══════════════════════════════════════════════════════════════════════════
# PYTHON GENERATOR EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

run_python_generator() {
    local generator="$1"
    shift
    local args="$@"
    
    local script="${PYTHON_DIR}/${generator}.py"
    
    if [[ ! -f "$script" ]]; then
        fatal "Generator script not found: $script"
    fi
    
    debug "Running Python generator: $generator"
    
    (
        source "${VENV_PATH}/bin/activate" || fatal "Failed to activate venv"
        python3 "$script" $args || return 1
        deactivate
    ) || return 1
    
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════
# REPORT GENERATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

get_timestamp() {
    date "+%Y%m%d"
}

get_timestamp_iso() {
    date "+%Y-%m-%d %H:%M:%S UTC"
}

get_year_month() {
    date "+%Y%m"
}

get_fiscal_quarter() {
    # FY27 runs Feb-Jan, so map current month to quarter
    # Q1: Feb-Apr (months 2-4)
    # Q2: May-Jul (months 5-7)
    # Q3: Aug-Oct (months 8-10)
    # Q4: Nov-Jan (months 11-1)
    local month=$(date "+%m")
    
    if [[ $month -ge 2 && $month -le 4 ]]; then
        echo "1"
    elif [[ $month -ge 5 && $month -le 7 ]]; then
        echo "2"
    elif [[ $month -ge 8 && $month -le 10 ]]; then
        echo "3"
    else
        echo "4"
    fi
}

get_fiscal_year() {
    # FY27: Feb 2026 - Jan 2027
    # FY28: Feb 2027 - Jan 2028
    local month=$(date "+%m")
    local year=$(date "+%Y")
    
    if [[ $month -ge 2 ]]; then
        # Feb-Dec: Same fiscal year
        echo "FY$((year % 2000 + 1))"
    else
        # Jan: Previous fiscal year
        echo "FY$((year % 2000))"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

is_valid_json() {
    local json="$1"
    python3 -c "import json; json.loads('$json')" 2>/dev/null
    return $?
}

validate_file_exists() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        error "File not found: $file"
        return 1
    fi
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLING WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

trap_error() {
    local lineno=$1
    error "Script failed at line $lineno"
    exit 1
}

# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

init_automation() {
    info "═══════════════════════════════════════════════════════════════"
    info "Channel Director Automation: Initialization"
    info "═══════════════════════════════════════════════════════════════"
    info "Territory: $TERRITORY"
    info "Director: $DIRECTOR_NAME"
    info "Started: $(get_timestamp_iso)"
    info ""
    
    ensure_directories
    
    if [[ ! -f "${VENV_PATH}/bin/activate" ]]; then
        fatal "Virtual environment not found at: $VENV_PATH"
    fi
    
    info "✅ Initialization complete"
}

finish_automation() {
    local workflow="$1"
    local status="$2"
    
    info ""
    info "═══════════════════════════════════════════════════════════════"
    info "Workflow: $workflow"
    info "Status: $status"
    info "Completed: $(get_timestamp_iso)"
    info "═══════════════════════════════════════════════════════════════"
}

# ═══════════════════════════════════════════════════════════════════════════
# END OF FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
