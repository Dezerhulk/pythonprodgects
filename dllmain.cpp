#include "pch.h"       // Precompiled header (must be first)
#include <windows.h>
#include <objbase.h>   // For CoTaskMemAlloc/CoTaskMemFree
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <sstream>
#include <mutex>
#include <memory>
#include <fstream>

// Optional API header
#if __has_include("nexus_fragments_api.h")
#include "nexus_fragments_api.h"
#endif

#ifndef NEXUSF_HANDLE
typedef void* NEXUSF_HANDLE;
#endif

// Logging function for debugging
static void log_error(const char* msg) {
    std::ofstream log("nexusf_dll_error.log", std::ios::app);
    if (log.is_open()) {
        log << "[" << GetTickCount() << "] " << msg << std::endl;
    }
}

// BufferSpace structure for managing buffer operations
struct BufferSpace {
    std::vector<uint8_t> buf;
    size_t length;
    BufferSpace(size_t len) : buf(len, 0), length(len) {
        if (len == 0) {
            log_error("BufferSpace: Zero length buffer");
            throw std::bad_alloc();
        }
    }
    bool operate(const std::string& op, int64_t idx, uint32_t value) {
        if (idx < 0 || static_cast<size_t>(idx) >= length) {
            std::stringstream ss;
            ss << "BufferSpace::operate: Invalid index " << idx << " (length=" << length << ")";
            log_error(ss.str().c_str());
            return false;
        }
        uint8_t& cell = buf[static_cast<size_t>(idx)];
        if (op == "add") cell += static_cast<uint8_t>(value);
        else if (op == "and") cell &= static_cast<uint8_t>(value);
        else if (op == "xor") cell ^= static_cast<uint8_t>(value);
        else if (op == "write") cell = static_cast<uint8_t>(value);
        else {
            log_error("BufferSpace::operate: Invalid operation");
            return false;
        }
        return true;
    }
};

// NexusF structure for managing buffer and thread safety
struct NexusF {
    std::unique_ptr<BufferSpace> buf;
    std::mutex mtx;
    NexusF(size_t sz) : buf(std::make_unique<BufferSpace>(sz)) {}
};

// Helper functions
static std::wstring make_temp_path(const wchar_t* prefix) {
    wchar_t tmp[MAX_PATH] = { 0 };
    if (GetTempPathW(MAX_PATH, tmp) == 0) {
        log_error("make_temp_path: GetTempPathW failed");
        wcscpy_s(tmp, L".");
    }
    wchar_t name[MAX_PATH];
    wsprintfW(name, L"%s\\%s_%u.csv", tmp, prefix, static_cast<unsigned int>(GetTickCount()));
    return std::wstring(name);
}

static wchar_t* alloc_wstring(const std::wstring& s) {
    size_t cch = s.size();
    wchar_t* out = static_cast<wchar_t*>(CoTaskMemAlloc((cch + 1) * sizeof(wchar_t)));
    if (!out) {
        log_error("alloc_wstring: CoTaskMemAlloc failed");
        return nullptr;
    }
    wcscpy_s(out, cch + 1, s.c_str());
    return out;
}

// Exported API functions
extern "C" {

    __declspec(dllexport) NEXUSF_HANDLE __stdcall nexusf_create(unsigned int buffer_size) {
        if (buffer_size == 0 || buffer_size > (1 << 26)) {
            log_error("nexusf_create: Invalid buffer size");
            return nullptr;
        }
        try {
            NexusF* n = new NexusF(buffer_size);
            if (!n->buf) {
                log_error("nexusf_create: Buffer allocation failed");
                delete n;
                return nullptr;
            }
            return n;
        }
        catch (const std::bad_alloc& e) {
            log_error("nexusf_create: Memory allocation exception");
            return nullptr;
        }
        catch (...) {
            log_error("nexusf_create: Unknown exception");
            return nullptr;
        }
    }

    __declspec(dllexport) void __stdcall nexusf_destroy(NEXUSF_HANDLE h) {
        if (!h) {
            log_error("nexusf_destroy: Null handle");
            return;
        }
        try {
            delete static_cast<NexusF*>(h);
        }
        catch (...) {
            log_error("nexusf_destroy: Exception during deletion");
        }
    }

    __declspec(dllexport) int __stdcall nexusf_run_test(
        NEXUSF_HANDLE h, int32_t SI, int32_t BX, int32_t DI, int32_t BP, int32_t iVar18, int32_t iVar19, int32_t uVar17, int32_t uVar8,
        wchar_t** csv_out_path)
    {
        HRESULT hr = CoInitialize(nullptr); // Initialize COM
        if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
            log_error("nexusf_run_test: CoInitialize failed");
            return 4;
        }

        if (!h || !csv_out_path) {
            log_error("nexusf_run_test: Invalid handle or output path");
            CoUninitialize();
            return 1;
        }

        NexusF* n = static_cast<NexusF*>(h);
        std::lock_guard<std::mutex> lk(n->mtx);

        // Validate indices to prevent buffer overflows
        int64_t idx1 = static_cast<int64_t>(SI) + BX + 0x72;
        int64_t idx2 = static_cast<int64_t>(DI) + BP + 99;
        int64_t idx3 = static_cast<int64_t>(uVar17) + iVar19 + 0x92c;

        if (idx1 < 0 || static_cast<size_t>(idx1) >= n->buf->length ||
            idx2 < 0 || static_cast<size_t>(idx2) >= n->buf->length ||
            idx3 < 0 || static_cast<size_t>(idx3) >= n->buf->length) {
            std::stringstream ss;
            ss << "nexusf_run_test: Invalid index (idx1=" << idx1 << ", idx2=" << idx2 << ", idx3=" << idx3 << ")";
            log_error(ss.str().c_str());
            CoUninitialize();
            return 2;
        }

        // Perform buffer operations
        if (!n->buf->operate("add", idx1, 0x12) ||
            !n->buf->operate("and", idx2, 0x7F) ||
            !n->buf->operate("write", idx3, uVar8 & 0xFF)) {
            log_error("nexusf_run_test: Buffer operation failed");
            CoUninitialize();
            return 3;
        }

        // Generate output path
        std::wstring path = make_temp_path(L"nexus_frag");
        *csv_out_path = alloc_wstring(path);
        if (!*csv_out_path) {
            log_error("nexusf_run_test: String allocation failed");
            CoUninitialize();
            return 5;
        }

        CoUninitialize();
        return 0;
    }

    __declspec(dllexport) int __stdcall nexusf_run_default(NEXUSF_HANDLE h, wchar_t** csv_out_path) {
        HRESULT hr = CoInitialize(nullptr); // Initialize COM
        if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
            log_error("nexusf_run_default: CoInitialize failed");
            return 4;
        }

        if (!h || !csv_out_path) {
            log_error("nexusf_run_default: Invalid handle or output path");
            CoUninitialize();
            return 1;
        }

        NexusF* n = static_cast<NexusF*>(h);
        std::lock_guard<std::mutex> lk(n->mtx);

        std::wstring path = make_temp_path(L"nexus_frag_default");
        *csv_out_path = alloc_wstring(path);
        if (!*csv_out_path) {
            log_error("nexusf_run_default: String allocation failed");
            CoUninitialize();
            return 5;
        }

        CoUninitialize();
        return 0;
    }

    __declspec(dllexport) void __stdcall nexusf_free_string(wchar_t* s) {
        if (s) {
            CoTaskMemFree(s);
        }
        else {
            log_error("nexusf_free_string: Null pointer");
        }
    }

} // extern "C"

// DLL entry point
BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    (void)hModule; (void)lpReserved;
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        log_error("DllMain: DLL_PROCESS_ATTACH");
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
