/*
 * Goldengames UMTX2 hand-off stage.
 *
 * elfldr needs an ELF to complete the kernel exploit, but the upstream
 * unified autoloader is not suitable here: it reads autoload.txt and may
 * launch a stale HEN before the dashboard can send the user's selection.
 * This intentionally inert payload returns immediately. The dashboard then
 * reconnects to elfldr and sends only the payload card the user pressed.
 */
int main(void) {
    return 0;
}
