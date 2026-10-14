#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
/* Optional host adaptation for a virtual PID namespace whose getpid() does
 * not match numeric /proc entries. Redirect ONLY this process's executable
 * lookup to the equivalent /proc/self/exe. Never used by default or in CI.
 * Does not change Lean's kernel, reductions, proof checking, or code generator.
 */
ssize_t readlink(const char *path, char *buf, size_t size) {
    ssize_t (*real_readlink)(const char *, char *, size_t) = dlsym(RTLD_NEXT, "readlink");
    char own[64];
    snprintf(own, sizeof own, "/proc/%ld/exe", (long)getpid());
    return real_readlink(strcmp(path, own) == 0 ? "/proc/self/exe" : path, buf, size);
}
