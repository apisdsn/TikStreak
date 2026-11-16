(() => {
  const $ = (id) => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";
  const ACCT_KEY = "bara_account";
  const LANG_KEY = "bara_lang";
  const THEME_KEY = "bara_theme";
  // pindahkan kunci localStorage lama (streak_panel_*) ke kunci baru; hapus yang lama
  try {
    [["bara_account", "streak_panel_account"], ["bara_lang", "streak_panel_lang"], ["bara_theme", "streak_panel_theme"]].forEach(([nk, ok]) => {
      if (localStorage.getItem(nk) === null && localStorage.getItem(ok) !== null) localStorage.setItem(nk, localStorage.getItem(ok));
      localStorage.removeItem(ok);
    });
  } catch (e) { /* storage tidak tersedia */ }

  // ------------------------------------------------------------------ i18n
  // Semua teks UI memakai Title Case (konektor selain kata pertama tetap huruf kecil)
  const I18N = {
    id: {
      brand: "Bara", loginHint: "Masuk dengan Nama Pengguna dan Kata Sandi", accessKey: "Kunci Akses", signIn: "Masuk",
      wrongKey: "Kunci Akses Salah", navLabel: "Navigasi Utama", navDashboard: "Dashboard", navAccounts: "Akun & Jadwal",
      navContacts: "Kontak", navCookies: "Cookie & Login", navSettings: "Pengaturan", language: "Bahasa", toggleTheme: "Ganti Tema",
      activeAccount: "Akun Aktif", signOut: "Keluar", nextSchedule: "Jadwal Berikutnya", customMessagePh: "Pesan Khusus (Opsional)",
      sendNow: "Kirim Sekarang", dryRun: "Uji Tanpa Kirim", stop: "Hentikan", streakDays: "Hari Beruntun", todayGoal: "Target Hari Ini",
      last7Days: "7 Hari Terakhir", cookie: "Cookie", cookieRefresh: "Pembaruan Cookie", notifications: "Notifikasi", accounts: "Akun",
      today: "Hari Ini", latestLog: "Log Terakhir", viewScreenshot: "Lihat Tangkapan Layar", history: "Riwayat", clearHistory: "Hapus Riwayat",
      colTime: "Waktu", colAccount: "Akun", colType: "Jenis", colResult: "Hasil", colDuration: "Durasi", colStatus: "Status",
      accountsHint: "Kelola Akun TikTok dan Jadwal Kirim", newAccountName: "Nama Akun Baru", newAccountPh: "Contoh: Akun Kedua",
      addAccount: "Tambah Akun", sendSchedules: "Jadwal Kirim", schedulesHint: "Atur Jam, Pesan, dan Penerima untuk Setiap Jadwal",
      schedulesSaveHint: "Tekan Simpan Jadwal untuk Menerapkan Perubahan", saveSchedules: "Simpan Jadwal", addSchedule: "Tambah Jadwal",
      contactsHint: "Kontak yang Menerima Pesan Streak", addContacts: "Tambah Kontak", contactsPh: "Satu Nama per Baris, Persis seperti di Daftar Pesan TikTok",
      add: "Tambah", contactList: "Daftar Kontak", account: "Akun", checkCookieNow: "Cek Cookie Sekarang", reLogin: "Login Ulang",
      idleNote: "Browser Server", remoteHint: "Buka Browser di Server, lalu Login ke TikTok dari Sini", startLogin: "Buka Browser Login",
      remoteBrowser: "Tampilan Browser Server", sendText: "Kirim Teks", sendTextPh: "Ketik lalu Tekan Enter",
      tip1: "Klik pada Layar untuk Memilih Kolom", tip2: "Gunakan Kolom Teks untuk Menempel Kata Sandi", tip3: "Setelah Login Terdeteksi, Simpan Sesi Login",
      saveLoginSession: "Simpan Sesi Login", cancel: "Batal", manualCookie: "Tempel Cookie Manual", manualCookieHint: "Alternatif Jika Login lewat Browser Server Gagal",
      cookiePh: "[{\"domain\": \".tiktok.com\", \"name\": \"sessionid\", \"value\": \"••••••••\", ...}, ...]", saveCookie: "Simpan Cookie", deleteCookie: "Hapus Cookie",
      settingsHint: "Atur Notifikasi, Pengguna, dan Pengaturan Global", message: "Pesan", defaultMessage: "Pesan Default", timezone: "Zona Waktu",
      keepalive: "Segarkan Cookie Otomatis", keepaliveHours: "Interval Penyegaran (Jam)", waits: "Waktu Tunggu (Detik)", pageLoad: "Muat Halaman",
      element: "Elemen", sendDelay: "Jeda Antar Kirim", proof: "Bukti", attachScreenshot: "Lampirkan Tangkapan Layar",
      attachScreenshotHint: "Kirim Tangkapan Layar Chat bersama Notifikasi", enableNotif: "Aktifkan Notifikasi", webhookUrl: "URL Webhook",
      testDiscord: "Kirim Pesan Uji Discord", botToken: "Token Bot", keepEmptyPh: "Kosongkan untuk Mempertahankan", chatId: "ID Chat",
      testTelegram: "Kirim Pesan Uji Telegram", save: "Simpan",
      // dari JS
      saved: "(Tersimpan)", ready: "Siap", busyAcct: "Berjalan: {name}", busy: "Berjalan",
      st_running: "Berjalan", st_success: "Berhasil", st_partial: "Sebagian", st_failed: "Gagal", st_cancelled: "Dihentikan",
      st_missed: "Terlewat", st_pending: "Menunggu",
      st_expired: "Terlewat", queued: "Dalam Antrean", queuePos: "Posisi {n}", queueEta: "Perkiraan {time}", runningState: "Sedang Berjalan",
      cancelJob: "Batalkan", toastJobCancelled: "Antrean Dibatalkan", queueLoad: "{n} Dalam Antrean",
      showing: "Menampilkan {a}–{b} dari {n}", showingNone: "Tidak Ada Data", fAll: "Semua", fSend: "Kirim", fCheck: "Cek Cookie", statusAll: "Semua Status",
      filterMode: "Filter Jenis", filterStatus: "Filter Status", pageSizeLbl: "Baris per Halaman", perPage: "{n} per Halaman", prevPage: "Halaman Sebelumnya",
      nextPage: "Halaman Berikutnya", pageN: "Halaman {n}", noHistoryFiltered: "Tidak Ada Riwayat yang Cocok", pagination: "Navigasi Halaman",
      queueAdmin: "Antrean Browser", qWorkers: "Pekerja Browser", qQueued: "Dalam Antrean", qRunning: "Sedang Berjalan", qLoad: "Beban per Jam",
      qLogin: "Sesi Login", queueAdminFoot: "Hanya Hitungan, Tanpa Nama atau Isi Akun", qNoLoad: "Belum Ada Jadwal Aktif",
      busyHint: "Jam Ini Ramai, Pilih Jam Lain agar Lebih Cepat",
      noSchedule: "Belum Ada Jadwal Aktif", noScheduleHint: "Tambahkan Jadwal di Tab Akun & Jadwal",
      allContacts: "Semua Kontak ({n})", nContacts: "{n} Kontak", nContacts1: "{n} Kontak",
      partMorning: "Pagi", partNoon: "Siang", partAfternoon: "Sore", partNight: "Malam",
      ringAria: "Sisa Waktu ke Jadwal Berikutnya: {time}", ringNone: "Tidak Ada Jadwal Berikutnya",
      cookieValid: "Valid", cookieInvalid: "Tidak Valid", cookieUnset: "Belum Diatur",
      checkedAgo: "Dicek {when}", notVerified: "Belum Diverifikasi", savedAgo: "Disimpan {when}",
      refreshEvery: "Setiap {n} Jam", refreshEvery1: "Setiap {n} Jam", refreshOff: "Nonaktif",
      refreshOn: "Menjaga Sesi Tetap Aktif", refreshOffSub: "Cookie Bisa Kedaluwarsa",
      notifOff: "Nonaktif", notifShot: "Dengan Tangkapan Layar", notifNoShot: "Tanpa Tangkapan Layar", notifNone: "Belum Ada Notifikasi",
      nAccounts: "{n} Akun", nAccounts1: "{n} Akun", totalContacts: "{n} Kontak Total",
      nSchedules: "{n} Jadwal", nSchedules1: "{n} Jadwal", emptyToday: "Belum Ada Jadwal Aktif Hari Ini",
      noHistory: "Belum Ada Riwayat", noContacts: "Belum Ada Kontak", noContactsHere: "Belum Ada Kontak di Akun Ini", noScheds: "Belum Ada Jadwal",
      typeSend: "Kirim", typeTest: "Uji", typeCheck: "Cek Cookie", trManual: "Manual", trAuto: "Otomatis",
      clickForLog: "Klik untuk Melihat Log", durMin: "{m} Mnt {s} Dtk", durSec: "{s} Dtk",
      confirmSend: "Kirim Pesan Streak ke Semua Kontak Akun {name} Sekarang?", confirmClear: "Hapus Semua Riwayat Anda?",
      confirmDeleteAccount: "Hapus Akun \"{name}\" beserta Cookie, Kontak, dan Jadwalnya?", confirmClearCookies: "Hapus Cookie Tersimpan?",
      promptAccountName: "Nama Akun:", promptRename: "Nama Baru untuk Kontak Ini (Persis seperti di Daftar Pesan TikTok):",
      toastStopping: "Menghentikan…", toastChecking: "Mengecek Cookie… Lihat Log di Dashboard", toastCookieSaved: "Cookie Disimpan",
      toastLoginSaved: "Login Tersimpan", toastSchedulesSaved: "Jadwal Disimpan", toastSettingsSaved: "Pengaturan Disimpan",
      toastTestSent: "Pesan Uji Terkirim", toastAdded: "{n} Kontak Ditambahkan", toastAccountCreated: "Akun \"{name}\" Dibuat. Atur Cookie di Tab Cookie",
      maxSchedules: "Maksimal 8 Jadwal",
      pick: "Pilih", picked: "Dipilih", rename: "Ubah Nama", del: "Hapus", renameAria: "Ubah Nama {name}", delAria: "Hapus {name}",
      acctMeta: "{contacts} · {cookie} · Berikutnya {next}", cookieBriefOk: "Cookie OK", cookieBriefSaved: "Cookie Tersimpan",
      cookieBriefBad: "Cookie Tidak Valid", cookieBriefNone: "Cookie Belum Diatur", noNext: "Tidak Ada",
      schedEnabled: "Jadwal Aktif", schedMsgPh: "Pesan Khusus (Kosong = Default)", sendToAll: "Kirim ke Semua Kontak", hour: "Jam", minute: "Menit",
      delSched: "Hapus Jadwal {time}", tzLabel: "Zona Waktu: {tz}", tzServer: "Server",
      bannerOk: "Cookie Valid", bannerBad: "Cookie Tidak Valid", bannerNone: "Cookie Belum Diatur", bannerNoneSub: "Pilih Salah Satu Cara di Bawah agar Panel Bisa Mengirim Pesan.",
      cookieCount: "{n} Cookie", warnNoSession: "Peringatan: Sessionid Tidak Ditemukan",
      step1: "Buka Browser", step2: "Login ke TikTok", step3: "Simpan Sesi",
      loginOpening: "Membuka Browser…", loginWaiting: "Menunggu Login…", loginDetected: "Login Terdeteksi. Klik Simpan Sesi Login",
      loginEnded: "Sesi Login Berakhir", loginCancelled: "Dibatalkan", loginSaved: "Berhasil: {n} Cookie Tersimpan",
      proofAlt: "Bukti {name}", evChat: "Chat Terverifikasi", evBubble: "Bubble Terverifikasi", evList: "Daftar Chat {time}",
      evRenamed: "Nama Baru {name}, Diperbarui Otomatis",
      rtNow: "Baru Saja", dash: "-",
      apiKey: "Kunci API", username: "Nama Pengguna", password: "Kata Sandi", confirmPassword: "Konfirmasi Kata Sandi",
      setupTitle: "Buat Admin Pertama", setupHint: "Isi Kunci API dari File .env, lalu Buat Akun Admin", createAdmin: "Buat Admin",
      passMismatch: "Konfirmasi Kata Sandi Tidak Sama", userMenu: "Menu Pengguna", roleAdmin: "Admin", roleUser: "Pengguna", role: "Peran",
      changePassword: "Ganti Kata Sandi", currentPassword: "Kata Sandi Saat Ini", newPassword: "Kata Sandi Baru", pwChanged: "Kata Sandi Diganti",
      myAccount: "Akun Saya", myNotifs: "Notifikasi Saya", myNotifsHint: "Notifikasi Hanya untuk Akun TikTok Milik Anda",
      discordNotif: "Notifikasi Discord", telegramNotif: "Notifikasi Telegram",
      adminNotifs: "Notifikasi Admin (Global)",
      adminOnlyNote: "Pengaturan Global Diatur oleh Admin",
      users: "Pengguna", addUser: "Tambah Pengguna", resetPw: "Reset Kata Sandi", makeAdmin: "Jadikan Admin", makeUser: "Jadikan Pengguna",
      disable: "Nonaktifkan", enable: "Aktifkan", disabledBadge: "Nonaktif", you: "Anda",
      confirmDeleteUser: "Hapus \"{name}\"? Pengguna Ini dan {n} Akun TikTok Miliknya Akan Dihapus Permanen.", confirmDisable: "Nonaktifkan Pengguna \"{name}\"?",
      promptNewPw: "Kata Sandi Baru untuk {name} (Minimal 8 Karakter):", toastUserAdded: "Pengguna Ditambahkan", toastUserUpdated: "Pengguna Diperbarui",
      toastUserDeleted: "Pengguna Dihapus", toastNotifSaved: "Notifikasi Disimpan", toastOwnerChanged: "Pemilik Akun Diubah",
      manageAccounts: "Kelola Akun", activeBadge: "Aktif", moreActions: "Aksi Lainnya",
      lastAccount: "Minimal Satu Akun", yourself: "Akun Anda Sendiri", cookiesHint: "Kelola Sesi Login TikTok", panelBusy: "Panel Sedang Dipakai",
      byLabel: "oleh {name}", wrongLogin: "Nama Pengguna atau Kata Sandi Salah",
      manualIntro: "Cara Termudah Adalah Login lewat Browser Server di Atas. Gunakan Cara Ini Jika Login Itu Gagal.",
      gs1t: "Buka TikTok di Laptop atau PC", gs1h: "Buka tiktok.com di Chrome atau Edge dan pastikan Anda sudah login ke akun TikTok yang benar.", gs1b: "Buka TikTok",
      gs2t: "Pasang Ekstensi Cookie-Editor", gs2h: "Ekstensi gratis untuk Chrome, Edge, dan Firefox. Klik tombol, lalu pilih “Add to Chrome” atau “Get”.", gs2b: "Pasang Cookie-Editor",
      gs3t: "Buka Cookie-Editor di Tab TikTok", gs3h: "Di tab tiktok.com, klik ikon puzzle (Ekstensi) di kanan atas, lalu pilih Cookie-Editor.",
      gs4t: "Ekspor sebagai JSON", gs4h: "Klik “Export” di bagian bawah, lalu pilih “JSON”. Cookie otomatis tersalin.",
      gs5t: "Tempel dan Simpan", gs5h: "Tempel (Ctrl+V) di kotak di bawah. Panel langsung memeriksanya, lalu tekan “Simpan Cookie”.",
      gs6t: "Periksa", gs6h: "Tekan “Cek Cookie Sekarang”. Banner di atas harus berubah hijau.",
      guideWarn: "Jangan Klik Logout di TikTok Laptop Setelah Menyalin, Cookie Akan Ikut Mati. Cukup Tutup Tabnya.",
      guidePrivacy: "Cookie Sama dengan Kunci Akun. Jangan Bagikan ke Orang Lain.",
      ckOk: "{n} Cookie Terbaca · sessionid Ditemukan", ckNoSession: "{n} Cookie Terbaca, tetapi sessionid Tidak Ada. Pastikan Anda Sudah Login di TikTok.",
      ckBad: "Format Tidak Dikenali. Ulangi Langkah 4.", ckFmtJson: "JSON", ckFmtHeader: "Header",
      reload: "Muat Ulang", manageUsers: "Kelola Pengguna", acctCount: "{n} Akun TikTok", acctCount1: "{n} Akun TikTok",
      confirmNewPassword: "Konfirmasi Kata Sandi Baru", pwHint: "Minimal 8 Karakter", pwSessionsHint: "Sesi di Perangkat Lain Akan Keluar",
      savePassword: "Simpan Kata Sandi", showPassword: "Tampilkan Kata Sandi", hidePassword: "Sembunyikan Kata Sandi",
      pwTooShort: "Kata Sandi Baru Minimal 8 Karakter", pwRequired: "Semua Kolom Wajib Diisi",
      tempPassword: "Kata Sandi Awal",
      tiktokAccounts: "Akun TikTok",
      navHomeS: "Beranda",
      navScheduleS: "Jadwal",
      navContactsS: "Kontak",
      navCookieS: "Cookie",
      navSettingsS: "Pengaturan",
      goodDays: "Hari Lancar",
      notSent: "Belum Dikirim",
      doneSlot: "Selesai {s}/{t}",
      nextAt: "Berikutnya {time}",
      pesanLabel: "Pesan:",
      cookieNotSet: "Cookie TikTok Belum Diatur",
      bothActive: "Keduanya Aktif",
      chOff: "{name} Nonaktif",
      allOff: "Discord & Telegram Nonaktif",
      eyebrowDefault: "",
      cookiesEyebrow: "Akun TikTok yang Sedang Dipilih",
      recommended: "Disarankan",
      opt1: "Cara 1: Login lewat Browser Server",
      opt1Sub: "Login Langsung dari Panel, Tanpa Menyalin Apa Pun.",
      opt2: "Cara 2: Tempel Cookie Manual",
      opt2Sub: "Gunakan Jika Cara 1 Gagal. Ikuti Langkah Berikut dari Laptop atau PC.",
      warnTitle: "Jangan Logout.",
      warnText: "Setelah Menyalin, Jangan Klik Logout di TikTok Laptop, Cookie Akan Ikut Mati. Cukup Tutup Tabnya.",
      privTitle: "Rahasiakan.",
      privText: "Cookie Sama dengan Kunci Akun. Jangan Bagikan ke Orang Lain.",
      pasteLabel: "Tempel Cookie di Sini",
      webhookDiscord: "URL Webhook Discord",
      sendTestMsg: "Kirim Pesan Uji",
      myNotifFoot: "Dikirim untuk Akun TikTok Milik Anda.",
      adminNotifFoot: "Saluran Global Hanya Menerima Notifikasi Akun Milik Admin dan Peringatan Sistem.",
      gChannels: "Discord & Telegram Global",
      gMessage: "Pesan & Zona Waktu",
      gWaits: "Waktu Tunggu",
      adminOnly: "Khusus Admin",
      adminBadge: "Masuk sebagai Admin",
      userBadge: "Masuk sebagai Pengguna",
      secUnit: "{s} Dtk",
      userMeta: "{n} · {state}",
      userMetaSelf: "Anda · {n}",
      stateActive: "Aktif",
      stateDisabled: "Nonaktif",
      enableTgDcFirst: "Aktifkan Discord atau Telegram Dulu",
      testSent: "Pesan Uji Terkirim",
      delSchedule: "Hapus Jadwal",
      delContact: "Hapus Kontak",
      roleGroup: "Peran",
      promptRenameLabel: "",
      notifOn: "Notifikasi Aktif",
      setSheetSave: "Simpan",
      pwOtherSessions: "Sesi di Perangkat Lain Akan Keluar",
      delUser: "Hapus Pengguna",
      timeLeft: "Sisa Waktu",
      remBack: "Kembali", remReload: "Muat Ulang", remLoginPage: "Buka Halaman Login", remTabN: "Tab {i}/{n}", remTabSwitch: "Ganti Tab",
      diagTitle: "Detail Teknis", diagEmpty: "Belum Ada Catatan",
      noRuns: "Belum Ada Proses", lbClose: "Tutup", lbDownload: "Unduh", lbPrev: "Sebelumnya", lbNext: "Berikutnya",
      lbLatestShot: "Tangkapan Layar Terakhir", reloadScreenshot: "Muat Ulang Tangkapan Layar", fullScreen: "Layar Penuh", lbZoomIn: "Klik untuk Ukuran Asli", lbZoomOut: "Klik untuk Muat Layar", lbViewer: "Penampil Gambar",
    },
    en: {
      brand: "Bara", loginHint: "Login with Your Username and Password", accessKey: "Access Key", signIn: "Login",
      wrongKey: "Wrong Access Key", navLabel: "Main Navigation", navDashboard: "Dashboard", navAccounts: "Accounts & Schedules",
      navContacts: "Contacts", navCookies: "Cookie & Login", navSettings: "Settings", language: "Language", toggleTheme: "Toggle Theme",
      activeAccount: "Active Account", signOut: "Log Out", nextSchedule: "Next Schedule", customMessagePh: "Custom Message (Optional)",
      sendNow: "Send Now", dryRun: "Test Without Sending", stop: "Stop", streakDays: "Day Streak", todayGoal: "Today's Goal",
      last7Days: "Last 7 Days", cookie: "Cookie", cookieRefresh: "Cookie Refresh", notifications: "Notifications", accounts: "Accounts",
      today: "Today", latestLog: "Latest Log", viewScreenshot: "View Screenshot", history: "History", clearHistory: "Clear History",
      colTime: "Time", colAccount: "Account", colType: "Type", colResult: "Result", colDuration: "Duration", colStatus: "Status",
      accountsHint: "Manage TikTok Accounts and Send Schedules", newAccountName: "New Account Name", newAccountPh: "Example: Second Account",
      addAccount: "Add Account", sendSchedules: "Send Schedules", schedulesHint: "Set the Time, Message, and Recipients for Each Schedule",
      schedulesSaveHint: "Press Save Schedules to Apply Changes", saveSchedules: "Save Schedules", addSchedule: "Add Schedule",
      contactsHint: "Contacts That Receive Streak Messages", addContacts: "Add Contacts", contactsPh: "One Name per Line, Exactly as in the TikTok Message List",
      add: "Add", contactList: "Contact List", account: "Account", checkCookieNow: "Check Cookie Now", reLogin: "Login Again",
      idleNote: "Server Browser", remoteHint: "Open a Browser on the Server, Then Login to TikTok from Here", startLogin: "Open Login Browser",
      remoteBrowser: "Server Browser View", sendText: "Send Text", sendTextPh: "Type Then Press Enter",
      tip1: "Click on the Screen to Select a Field", tip2: "Use the Text Field to Paste Passwords", tip3: "Once Login Is Detected, Save the Login Session",
      saveLoginSession: "Save Login Session", cancel: "Cancel", manualCookie: "Paste Cookie Manually", manualCookieHint: "Alternative if Login via Server Browser Fails",
      cookiePh: "[{\"domain\": \".tiktok.com\", \"name\": \"sessionid\", \"value\": \"••••••••\", ...}, ...]", saveCookie: "Save Cookie", deleteCookie: "Delete Cookie",
      settingsHint: "Manage Notifications, Users and Global Settings", message: "Message", defaultMessage: "Default Message", timezone: "Time Zone",
      keepalive: "Refresh Cookie Automatically", keepaliveHours: "Refresh Interval (Hours)", waits: "Wait Times (Seconds)", pageLoad: "Page Load",
      element: "Element", sendDelay: "Delay Between Sends", proof: "Proof", attachScreenshot: "Attach Screenshot",
      attachScreenshotHint: "Send a Chat Screenshot with the Notification", enableNotif: "Enable Notifications", webhookUrl: "Webhook URL",
      testDiscord: "Send Discord Test Message", botToken: "Bot Token", keepEmptyPh: "Leave Empty to Keep", chatId: "Chat ID",
      testTelegram: "Send Telegram Test Message", save: "Save",
      saved: "(Saved)", ready: "Ready", busyAcct: "Running: {name}", busy: "Running",
      st_running: "Running", st_success: "Success", st_partial: "Partial", st_failed: "Failed", st_cancelled: "Stopped",
      st_missed: "Missed", st_pending: "Pending",
      st_expired: "Missed", queued: "Queued", queuePos: "Position {n}", queueEta: "Estimated {time}", runningState: "In Progress",
      cancelJob: "Cancel", toastJobCancelled: "Job Cancelled", queueLoad: "{n} Queued",
      showing: "Showing {a}–{b} of {n}", showingNone: "No Data", fAll: "All", fSend: "Send", fCheck: "Check Cookie", statusAll: "All Statuses",
      filterMode: "Filter Type", filterStatus: "Filter Status", pageSizeLbl: "Rows per Page", perPage: "{n} per Page", prevPage: "Previous Page",
      nextPage: "Next Page", pageN: "Page {n}", noHistoryFiltered: "No Matching History", pagination: "Page Navigation",
      queueAdmin: "Browser Queue", qWorkers: "Browser Workers", qQueued: "Queued", qRunning: "In Progress", qLoad: "Load per Hour",
      qLogin: "Login Sessions", queueAdminFoot: "Counts Only, No Account Names or Contents", qNoLoad: "No Active Schedules Yet",
      busyHint: "This Time Is Busy, Pick Another Time for Faster Delivery",
      noSchedule: "No Active Schedule", noScheduleHint: "Add One in the Accounts & Schedules Tab",
      allContacts: "All Contacts ({n})", nContacts: "{n} Contacts", nContacts1: "{n} Contact",
      partMorning: "Morning", partNoon: "Noon", partAfternoon: "Afternoon", partNight: "Night",
      ringAria: "Time Left to Next Schedule: {time}", ringNone: "No Next Schedule",
      cookieValid: "Valid", cookieInvalid: "Invalid", cookieUnset: "Not Set",
      checkedAgo: "Checked {when}", notVerified: "Not Verified Yet", savedAgo: "Saved {when}",
      refreshEvery: "Every {n} Hours", refreshEvery1: "Every {n} Hour", refreshOff: "Off",
      refreshOn: "Keeps the Session Alive", refreshOffSub: "Cookie May Expire",
      notifOff: "Off", notifShot: "With Screenshots", notifNoShot: "Without Screenshots", notifNone: "No Notifications Yet",
      nAccounts: "{n} Accounts", nAccounts1: "{n} Account", totalContacts: "{n} Contacts Total",
      nSchedules: "{n} Schedules", nSchedules1: "{n} Schedule", emptyToday: "No Active Schedules Today",
      noHistory: "No History Yet", noContacts: "No Contacts Yet", noContactsHere: "No Contacts in This Account", noScheds: "No Schedules Yet",
      typeSend: "Send", typeTest: "Test", typeCheck: "Cookie Check", trManual: "Manual", trAuto: "Automatic",
      clickForLog: "Click to View Log", durMin: "{m}m {s}s", durSec: "{s}s",
      confirmSend: "Send Streak Message to All Contacts of {name} Now?", confirmClear: "Delete All of Your History?",
      confirmDeleteAccount: "Delete Account \"{name}\" with Its Cookies, Contacts, and Schedules?", confirmClearCookies: "Delete Saved Cookie?",
      promptAccountName: "Account Name:", promptRename: "New Name for This Contact (Exactly as in the TikTok Message List):",
      toastStopping: "Stopping…", toastChecking: "Checking Cookie… See the Log on the Dashboard", toastCookieSaved: "Cookie Saved",
      toastLoginSaved: "Login Saved", toastSchedulesSaved: "Schedules Saved", toastSettingsSaved: "Settings Saved",
      toastTestSent: "Test Message Sent", toastAdded: "{n} Contacts Added", toastAccountCreated: "Account \"{name}\" Created. Set Its Cookie in the Cookies Tab",
      maxSchedules: "Maximum 8 Schedules",
      pick: "Select", picked: "Selected", rename: "Rename", del: "Delete", renameAria: "Rename {name}", delAria: "Delete {name}",
      acctMeta: "{contacts} · {cookie} · Next {next}", cookieBriefOk: "Cookie OK", cookieBriefSaved: "Cookie Saved",
      cookieBriefBad: "Cookie Invalid", cookieBriefNone: "Cookie Not Set", noNext: "None",
      schedEnabled: "Schedule Enabled", schedMsgPh: "Custom Message (Empty = Default)", sendToAll: "Send to All Contacts", hour: "Hour", minute: "Minute",
      delSched: "Delete Schedule {time}", tzLabel: "Time Zone: {tz}", tzServer: "Server",
      bannerOk: "Cookie Valid", bannerBad: "Cookie Invalid", bannerNone: "No Cookie Yet", bannerNoneSub: "Choose One of the Options Below So the Panel Can Send Messages.",
      cookieCount: "{n} Cookies", warnNoSession: "Warning: Sessionid Not Found",
      step1: "Open Browser", step2: "Login to TikTok", step3: "Save Session",
      loginOpening: "Opening Browser…", loginWaiting: "Waiting for Login…", loginDetected: "Login Detected. Click Save Login Session",
      loginEnded: "Login Session Ended", loginCancelled: "Cancelled", loginSaved: "Success: {n} Cookies Saved",
      proofAlt: "Proof {name}", evChat: "Chat Verified", evBubble: "Bubble Verified", evList: "Chat List {time}",
      evRenamed: "New Name {name}, Updated Automatically",
      rtNow: "Just Now", dash: "-",
      apiKey: "API Key", username: "Username", password: "Password", confirmPassword: "Confirm Password",
      setupTitle: "Create First Admin", setupHint: "Enter the API Key from the .env File, Then Create the Admin Account", createAdmin: "Create Admin",
      passMismatch: "Passwords Do Not Match", userMenu: "User Menu", roleAdmin: "Admin", roleUser: "User", role: "Role",
      changePassword: "Change Password", currentPassword: "Current Password", newPassword: "New Password", pwChanged: "Password Changed",
      myAccount: "My Account", myNotifs: "My Notifications", myNotifsHint: "Notifications Only for TikTok Accounts You Own",
      discordNotif: "Discord Notifications", telegramNotif: "Telegram Notifications",
      adminNotifs: "Admin Notifications (Global)",
      adminOnlyNote: "Global Settings Are Managed by the Admin",
      users: "Users", addUser: "Add User", resetPw: "Reset Password", makeAdmin: "Make Admin", makeUser: "Make User",
      disable: "Disable", enable: "Enable", disabledBadge: "Disabled", you: "You",
      confirmDeleteUser: "Delete \"{name}\"? This User and {n} TikTok Accounts Will Be Permanently Deleted.", confirmDisable: "Disable User \"{name}\"?",
      promptNewPw: "New Password for {name} (At Least 8 Characters):", toastUserAdded: "User Added", toastUserUpdated: "User Updated",
      toastUserDeleted: "User Deleted", toastNotifSaved: "Notifications Saved", toastOwnerChanged: "Account Owner Changed",
      manageAccounts: "Manage Accounts", activeBadge: "Active", moreActions: "More Actions",
      lastAccount: "At Least One Account", yourself: "Your Own Account", cookiesHint: "Manage TikTok Login Sessions", panelBusy: "Panel Is Busy",
      byLabel: "by {name}", wrongLogin: "Wrong Username or Password",
      manualIntro: "The Easiest Way Is Logging In via the Server Browser Above. Use This Method if That Login Fails.",
      gs1t: "Open TikTok on a Laptop or PC", gs1h: "Open tiktok.com in Chrome or Edge and make sure you are logged in to the right TikTok account.", gs1b: "Open TikTok",
      gs2t: "Install the Cookie-Editor Extension", gs2h: "A free extension for Chrome, Edge and Firefox. Click the button, then choose “Add to Chrome” or “Get”.", gs2b: "Install Cookie-Editor",
      gs3t: "Open Cookie-Editor on the TikTok Tab", gs3h: "On the tiktok.com tab, click the puzzle (Extensions) icon at the top right, then choose Cookie-Editor.",
      gs4t: "Export as JSON", gs4h: "Click “Export” at the bottom, then choose “JSON”. The cookies are copied automatically.",
      gs5t: "Paste and Save", gs5h: "Paste (Ctrl+V) into the box below. The panel checks it right away, then press “Save Cookie”.",
      gs6t: "Verify", gs6h: "Press “Check Cookie Now”. The banner at the top should turn green.",
      guideWarn: "Do Not Click Logout on the Laptop TikTok After Copying, or the Cookie Will Die. Just Close the Tab.",
      guidePrivacy: "A Cookie Is the Same as an Account Key. Never Share It with Anyone.",
      ckOk: "{n} Cookies Read · sessionid Found", ckOk1: "{n} Cookie Read · sessionid Found", ckNoSession: "{n} Cookies Read, but sessionid Is Missing. Make Sure You Are Logged In to TikTok.", ckNoSession1: "{n} Cookie Read, but sessionid Is Missing. Make Sure You Are Logged In to TikTok.",
      ckBad: "Unrecognised Format. Repeat Step 4.", ckFmtJson: "JSON", ckFmtHeader: "Header",
      reload: "Reload", manageUsers: "Manage Users", acctCount: "{n} TikTok Accounts", acctCount1: "{n} TikTok Account",
      confirmNewPassword: "Confirm New Password", pwHint: "At Least 8 Characters", pwSessionsHint: "Sessions on Other Devices Will Be Signed Out",
      savePassword: "Save Password", showPassword: "Show Password", hidePassword: "Hide Password",
      pwTooShort: "New Password Must Be at Least 8 Characters", pwRequired: "All Fields Are Required",
      tiktokAccounts: "TikTok Accounts",
      navHomeS: "Home",
      navScheduleS: "Schedule",
      navContactsS: "Contacts",
      navCookieS: "Cookie",
      navSettingsS: "Settings",
      goodDays: "Good Days",
      notSent: "Not Sent Yet",
      doneSlot: "Done {s}/{t}",
      nextAt: "Next at {time}",
      pesanLabel: "Message:",
      cookieNotSet: "TikTok Cookie Not Set",
      bothActive: "Both Active",
      chOff: "{name} Off",
      allOff: "Discord & Telegram Off",
      cookiesEyebrow: "Currently Selected TikTok Account",
      recommended: "Recommended",
      opt1: "Option 1: Login via the Server Browser",
      opt1Sub: "Login Right from the Panel, Nothing to Copy.",
      opt2: "Option 2: Paste Cookie Manually",
      opt2Sub: "Use This If Option 1 Fails. Follow These Steps on a Laptop or PC.",
      warnTitle: "Do Not Log Out.",
      warnText: "After Copying, Don’t Click Log Out on TikTok on Your Laptop, or the Cookie Dies Too. Just Close the Tab.",
      privTitle: "Keep It Private.",
      privText: "A Cookie Is Like Your Account Key. Never Share It.",
      pasteLabel: "Paste Cookie Here",
      webhookDiscord: "Discord Webhook URL",
      sendTestMsg: "Send Test Message",
      myNotifFoot: "Sent for the TikTok Accounts You Own.",
      adminNotifFoot: "The Global Channel Only Receives Notifications for the Admin’s Own Accounts and System Alerts.",
      gChannels: "Global Discord & Telegram",
      gMessage: "Message & Time Zone",
      gWaits: "Wait Times",
      adminOnly: "Admin Only",
      adminBadge: "Signed In as Admin",
      userBadge: "Signed In as User",
      secUnit: "{s} Sec",
      userMeta: "{n} · {state}",
      userMetaSelf: "You · {n}",
      stateActive: "Active",
      stateDisabled: "Disabled",
      tempPassword: "Initial Password",
      enableTgDcFirst: "Enable Discord or Telegram First",
      testSent: "Test Message Sent",
      delSchedule: "Delete Schedule",
      delContact: "Delete Contact",
      roleGroup: "Role",
      notifOn: "Notifications On",
      setSheetSave: "Save",
      pwOtherSessions: "Sessions on Other Devices Will Be Signed Out",
      delUser: "Delete User",
      timeLeft: "Time Left",
      remBack: "Back", remReload: "Reload", remLoginPage: "Open Login Page", remTabN: "Tab {i}/{n}", remTabSwitch: "Switch Tab",
      diagTitle: "Technical Details", diagEmpty: "No Entries Yet",
      noRuns: "No Runs Yet", lbClose: "Close", lbDownload: "Download", lbPrev: "Previous", lbNext: "Next",
      lbLatestShot: "Latest Screenshot", reloadScreenshot: "Reload Screenshot", fullScreen: "Full Screen", lbZoomIn: "Click for Actual Size", lbZoomOut: "Click to Fit Screen", lbViewer: "Image Viewer",
    },
  };
  const CONNECTORS = {
    id: new Set(["di", "ke", "dari", "dan", "atau", "yang", "untuk", "dengan", "pada", "per", "lewat", "lalu", "agar"]),
    en: new Set(["a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "at", "by", "with", "via", "as", "from", "per"]),
  };
  const LOCALE = { id: "id-ID", en: "en-US" };

  let lang = "id";
  let theme = "light";
  let me = null;            // {id, username, role}
  let users = [];
  let myNotif = null;
  let currentId = "";
  try {
    currentId = localStorage.getItem(ACCT_KEY) || "";
    const l = localStorage.getItem(LANG_KEY);
    if (l === "id" || l === "en") lang = l;
  } catch (e) { /* storage tidak tersedia */ }

  const KEEP_WORDS = new Set(["sessionid", "tiktok.com"]);
  const RAW_KEYS = new Set(["cookiePh"]);
  function titleCase(s) {
    let sentenceStart = true;  // kata pertama dan kata setelah . ! ? selalu berhuruf besar
    return String(s).split(/(\s+)/).map((w, i) => {
      if (!w.trim() || w.includes("{")) return w;
      const first = sentenceStart;
      sentenceStart = /[.!?]$/.test(w);
      if (KEEP_WORDS.has(w.replace(/[.,:;()?!]+$/, "").toLowerCase())) return w;
      const core = w.replace(/^[“"'(\[]+|[”"'),.:;!?\]]+$/g, "").toLowerCase();
      if (!first && CONNECTORS[lang].has(core)) return w.replace(/[\p{L}]+/u, core);
      return w.replace(/\p{L}/u, (c) => c.toUpperCase());
    }).join("");
  }

  // Terjemahan + Title Case, lalu isi placeholder {x}
  function t(key, vars) {
    const raw = I18N[lang][key] ?? I18N.id[key] ?? key;
    if (RAW_KEYS.has(key)) return raw;
    let s = titleCase(raw);
    if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m));
    return s;
  }
  // Bentuk jamak/tunggal: key1 dipakai bila n == 1
  const tn = (key, n) => t(n === 1 && I18N[lang][key + "1"] ? key + "1" : key, { n });

  // ------------------------------------------------------------------ state
  let accounts = [];
  let serverNow = "";
  let st = null;            // /api/status terakhir
  let settings = null;
  let hist = { items: [], total: 0, page: 1, page_size: 20 };  // halaman riwayat aktif
  let dash = null;          // /api/dashboard untuk akun terpilih
  let histSeq = 0;
  const HIST_KEY = "bara_history";
  const loadHF = () => {
    const d = { page: 1, size: 20, mode: "", status: "" };
    try {
      const v = JSON.parse(localStorage.getItem(HIST_KEY) || "{}");
      if ([10, 20, 50].includes(v.size)) d.size = v.size;
      if (Number.isInteger(v.page) && v.page > 0) d.page = v.page;
      if (["send", "check"].includes(v.mode)) d.mode = v.mode;
      if (["success", "partial", "failed", "expired", "cancelled"].includes(v.status)) d.status = v.status;
    } catch (e) { /* abaikan */ }
    return d;
  };
  let hf = loadHF();
  const saveHF = () => { try { localStorage.setItem(HIST_KEY, JSON.stringify(hf)); } catch (e) { /* abaikan */ } };
  let contactList = [];
  let logCursor = 0;
  let lastRunId = null;
  let pinned = false;       // true saat melihat log dari riwayat
  let pollTimer = null;
  let histTimer = null;
  let wasRunning = false;
  let dashSig = "";
  let loginTimer = null;
  let framePending = false;
  let loginMode = "idle";   // idle | open | logged
  let loginMsg = null;      // {key, vars, raw, cls}

  // ---------------------------------------------------------------- helpers
  async function api(path, opts = {}) {
    const res = await fetch("/api" + path, {
      credentials: "same-origin",
      method: opts.method || "GET",
      headers: { "X-Requested-With": "bara", ...(opts.body ? { "Content-Type": "application/json" } : {}) },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 401 && !path.startsWith("/auth/")) { showLogin(); throw new Error("Unauthorized"); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  }
  const apiA = (path, opts) => api(path + (path.includes("?") ? "&" : "?") + "account=" + encodeURIComponent(currentId), opts);
  const curAccount = () => accounts.find((a) => a.id === currentId) || accounts[0];

  function el(tag, props = {}, children = []) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k.includes("-") || k === "role") n.setAttribute(k, v);
      else n[k] = v;
    }
    children.forEach((c) => n.append(c));
    return n;
  }
  function icon(id, cls) {
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("aria-hidden", "true");
    if (cls) s.setAttribute("class", cls);
    const u = document.createElementNS(NS, "use");
    u.setAttribute("href", "#" + id);
    s.append(u);
    return s;
  }
  const setText = (id, text) => { $(id).textContent = text; };
  const pad = (n) => String(n).padStart(2, "0");
  const clamp = (n, a, b) => Math.min(b, Math.max(a, n));
  // warna avatar deterministik per id (dipakai sama di mana pun id itu tampil)
  const AV = [["#FF6A00", "#1C1C1E"], ["#0A84FF", "#FFFFFF"], ["#BF5AF2", "#FFFFFF"], ["#30D158", "#0B3D1A"], ["#FF375F", "#FFFFFF"], ["#40C8E0", "#062A33"], ["#FF9F0A", "#1C1C1E"], ["#5E5CE6", "#FFFFFF"]];
  const avColor = (id) => { let h = 0; for (const ch of String(id || "")) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return AV[h % AV.length]; };
  function paint(node, id) { const [bg, fg] = avColor(id); node.style.background = bg; node.style.color = fg; return node; }

  function toast(msg) {
    const e = $("toast");
    e.textContent = msg;
    e.classList.remove("hidden");
    clearTimeout(toast.t);
    toast.t = setTimeout(() => e.classList.add("hidden"), 2500);
  }

  // Pesan yang bisa berupa teks terjemahan (hint) atau error dari server
  function setMsg(id, text, hintKey) {
    const e = $(id);
    if (text) { e.removeAttribute("data-i18n"); e.textContent = text; }
    else if (hintKey) { e.setAttribute("data-i18n", hintKey); e.textContent = t(hintKey); }
    else e.textContent = "";
  }

  // Waktu server bersifat naive (tanpa zona), jadi semua selisih dihitung antar string server
  const parseNaive = (iso) => new Date(iso);
  const dayOf = (iso) => (iso || "").slice(0, 10);
  const hhmmOf = (iso) => (iso || "").slice(11, 16);
  function addDays(day, n) {
    const d = new Date(day + "T12:00:00Z");
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }
  const dayDate = (day) => new Date(day + "T12:00:00Z");

  function relTime(iso) {
    if (!iso || !serverNow) return "";
    const sec = Math.round((parseNaive(serverNow) - parseNaive(iso)) / 1000);
    const rtf = new Intl.RelativeTimeFormat(LOCALE[lang], { numeric: "auto" });
    let s;
    if (sec < 45) s = t("rtNow");
    else if (sec < 3600) s = rtf.format(-Math.round(sec / 60), "minute");
    else if (sec < 86400) s = rtf.format(-Math.round(sec / 3600), "hour");
    else s = rtf.format(-Math.round(sec / 86400), "day");
    if (lang === "id") s = s.replace(" yang lalu", " lalu");
    return titleCase(s);
  }

  function fmtDateTime(iso) {
    if (!iso) return "-";
    const d = new Intl.DateTimeFormat(LOCALE[lang], { day: "numeric", month: "short", timeZone: "UTC" }).format(dayDate(dayOf(iso)));
    return titleCase(`${d} ${hhmmOf(iso)}`);
  }

  function duration(r) {
    if (!r.started_at || !r.finished_at) return "-";
    const sec = Math.max(0, Math.round((parseNaive(r.finished_at) - parseNaive(r.started_at)) / 1000));
    return sec >= 60 ? t("durMin", { m: Math.floor(sec / 60), s: pad(sec % 60) }) : t("durSec", { s: sec });
  }

  const partKey = (h) => (h < 11 ? "partMorning" : h < 15 ? "partNoon" : h < 18 ? "partAfternoon" : "partNight");
  const partName = (h) => t(partKey(h));
  const slotPart = (time) => partName(parseInt(time.slice(0, 2), 10));

  function badge(status, label) {
    return el("span", { className: "badge " + status, textContent: label || t("st_" + status) });
  }
  const statusLabel = (s) => (I18N.id["st_" + s] ? t("st_" + s) : s);

  // ------------------------------------------------------------- theme / lang
  function applyTheme(th) {
    theme = th;
    document.documentElement.dataset.theme = th;
    const m = document.querySelector('meta[name="theme-color"]');
    if (m) m.content = th === "dark" ? "#000000" : "#EEF2F8";
    document.querySelectorAll("#themeBtn use, #loginTheme use").forEach((u) => u.setAttribute("href", th === "dark" ? "#i-sun" : "#i-moon"));
  }
  function toggleTheme() {
    applyTheme(theme === "dark" ? "light" : "dark");
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* abaikan */ }
  }
  let initialTheme = "light";
  try {
    initialTheme = localStorage.getItem(THEME_KEY) || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  } catch (e) { /* abaikan */ }
  applyTheme(initialTheme === "dark" ? "dark" : "light");
  $("themeBtn").addEventListener("click", toggleTheme);
  $("loginTheme").addEventListener("click", toggleTheme);

  const TAB_KEYS = { dashboard: "navDashboard", accounts: "navAccounts", contacts: "navContacts", cookies: "navCookies", settings: "navSettings" };
  function applyStaticI18n() {
    document.querySelectorAll("#tabs [data-tab]").forEach((b) => {
      const label = t(TAB_KEYS[b.dataset.tab]);
      b.setAttribute("aria-label", label);
      b.title = label;
    });
    const map = { i18n: (n, v) => { n.textContent = v; }, "i18n-ph": (n, v) => { n.placeholder = v; },
      "i18n-aria": (n, v) => n.setAttribute("aria-label", v), "i18n-title": (n, v) => { n.title = v; },
      "i18n-alt": (n, v) => { n.alt = v; } };
    for (const [attr, fn] of Object.entries(map)) {
      document.querySelectorAll(`[data-${attr}]`).forEach((n) => fn(n, t(n.getAttribute("data-" + attr))));
    }
  }

  function setLang(l) {
    lang = l;
    try { localStorage.setItem(LANG_KEY, l); } catch (e) { /* abaikan */ }
    document.documentElement.lang = l;
    document.querySelectorAll(".segmented [data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === l)));
    applyStaticI18n();
    renderLoginMode();
    renderLoginMsg();
    renderLoginSteps();
    $("loginLangCode").textContent = l.toUpperCase();
    $("loginLang").setAttribute("aria-label", `${t("language")}: ${l.toUpperCase()}`);
    $("loginLang").title = $("loginLang").getAttribute("aria-label");
    renderAll();
  }
  $("loginLang").addEventListener("click", () => setLang(lang === "id" ? "en" : "id"));
  document.querySelectorAll(".segmented [data-lang]").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.lang)));

  // ------------------------------------------------------------------- auth
  let setupMode = false;
  const isAdmin = () => !!me && me.role === "admin";

  function renderLoginMode() {
    $("loginTitle").textContent = t(setupMode ? "setupTitle" : "brand");
    $("loginHint").textContent = t(setupMode ? "setupHint" : "loginHint");
    $("loginSubmit").textContent = t(setupMode ? "createAdmin" : "signIn");
    $("fieldSetupKey").classList.toggle("hidden", !setupMode);
    $("fieldPass2").classList.toggle("hidden", !setupMode);
    $("setupKey").required = $("loginPass2").required = setupMode;
    $("loginPass").autocomplete = setupMode ? "new-password" : "current-password";
  }

  function showLogin() {
    $("app").classList.add("hidden");
    $("login").classList.remove("hidden");
    clearInterval(pollTimer);
    clearInterval(histTimer);
    closeMenu();
    closePwModal(true);
    closeSetSheet(true);
    me = null;
    renderLoginMode();
  }

  function applyRole() {
    $("userBtnName").textContent = me.username;
    $("userAvatar").textContent = initial(me.username);
    paint($("userAvatar"), me.id);
    $("userBtn").title = me.username;
    $("adminArea").classList.toggle("hidden", !isAdmin());
    $("usersCol").classList.toggle("hidden", !isAdmin());
    $("settingsGrid").classList.toggle("solo", !isAdmin());
    $("adminNote").classList.toggle("hidden", isAdmin());
    $("roleBadge").textContent = t(isAdmin() ? "adminBadge" : "userBadge");
  }

  async function enter() {
    st = await api("/status");
    me = st.user;
    serverNow = st.server_now || serverNow;
    syncAccounts(st.accounts);
    $("login").classList.add("hidden");
    $("app").classList.remove("hidden");
    applyRole();
    await Promise.all([loadSettings(), loadMyNotif(), loadContacts(), loadHistory(), loadSlots(), isAdmin() ? Promise.all([loadUsers(), loadQueueAdmin()]) : Promise.resolve()]);
    renderSchedules(curAccount().schedules);
    renderAll();
    await refresh();
    clearInterval(pollTimer);
    clearInterval(histTimer);
    pollTimer = setInterval(refresh, 2000);
    histTimer = setInterval(() => { loadHistory().catch(() => {}); loadSlots(); loadQueueAdmin(); }, 30000);
  }

  // Reset data per sesi agar pengguna berikutnya tidak melihat sisa data
  function resetSession() {
    accounts = []; hist = { items: [], total: 0, page: 1, page_size: 20 }; dash = null; contactList = []; users = []; st = null; settings = null; myNotif = null;
    lastRunId = null; logCursor = 0; pinned = false; idleLogKey = null; dashSig = "";
    $("logBox").replaceChildren(); $("proofBox").replaceChildren(); setRunBadge("");
    $("historyBody").replaceChildren(); $("scheduleList").replaceChildren();
    $("shotView").classList.add("hidden");
    if (shotUrl) { URL.revokeObjectURL(shotUrl); shotUrl = null; }
    renderShotButtons();
    renderAccountList.sig = null;
  }

  $("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("loginErr");
    err.textContent = "";
    const username = $("loginUser").value.trim();
    const password = $("loginPass").value;
    try {
      if (setupMode) {
        if (password !== $("loginPass2").value) { err.textContent = t("passMismatch"); return; }
        await api("/auth/setup", { method: "POST", body: { api_key: $("setupKey").value.trim(), username, password } });
      } else {
        await api("/auth/login", { method: "POST", body: { username, password } });
      }
      $("loginPass").value = $("loginPass2").value = $("setupKey").value = "";
      setupMode = false;
      resetSession();
      await enter();
    } catch (ex) {
      err.textContent = ex.message;
      showLogin();
    }
  });

  async function logout() {
    try { await api("/auth/logout", { method: "POST" }); } catch (e) { /* abaikan */ }
    resetSession();
    showLogin();
  }

  async function initAuth() {
    try {
      const s = await api("/auth/state");
      setupMode = s.setup_required;
      if (s.user) { await enter(); return; }
    } catch (e) { /* tampilkan login */ }
    showLogin();
  }

  // ------------------------------------------------- menu popover & sheet
  let menuEl = null, menuAnchor = null, menuOnClose = null;
  function closeMenu(restore = true) {
    if (!menuEl) return;
    menuEl.remove();
    menuEl = null;
    if (menuAnchor) {
      menuAnchor.setAttribute("aria-expanded", "false");
      if (restore) menuAnchor.focus();
    }
    menuAnchor = null;
  }
  // items: {label, onClick, role, checked, danger, disabled, reason, avatar, dot, sep}
  function openMenu(anchor, items, label, opts = {}) {
    const same = menuAnchor === anchor;
    closeMenu(false);
    if (same) return;
    const m = el("div", { className: "menu" + (opts.className ? " " + opts.className : ""), role: "menu", "aria-label": label || "" });
    items.forEach((it) => {
      if (it.sep) { m.append(el("hr", { role: "separator" })); return; }
      if (it.header) {
        m.append(el("div", { className: "menu-head" }, [
          paint(el("span", { className: "avatar-sm", textContent: it.avatar, "aria-hidden": "true" }), it.avatarId),
          el("div", { className: "mh-txt" }, [el("div", { className: "mh-name", textContent: it.title }), el("div", { className: "mh-sub", textContent: it.sub })]),
        ]));
        return;
      }
      const b = el("button", { type: "button", role: it.role || "menuitem", disabled: !!it.disabled });
      if (it.role === "menuitemradio") b.setAttribute("aria-checked", String(!!it.checked));
      if (it.danger) b.classList.add("danger");
      if (it.icon) b.append(icon(it.icon, "m-ico"));
      if (it.avatar) b.append(paint(el("span", { className: "avatar-sm", textContent: it.avatar, "aria-hidden": "true" }), it.avatarId));
      const lab = el("span", { className: "m-label", textContent: it.label });
      if (it.reason) lab.append(el("span", { className: "m-reason", textContent: it.reason }));
      b.append(lab);
      if (it.dot) b.append(el("span", { className: "dot " + it.dot, "aria-hidden": "true" }));
      if (it.role === "menuitemradio") b.append(icon("i-check", "tick"));
      b.addEventListener("click", () => { closeMenu(false); if (it.onClick) it.onClick(); });
      m.append(b);
    });
    document.body.append(m);
    const r = anchor.getBoundingClientRect();
    const w = Math.max(240, Math.min(m.offsetWidth, 340));
    m.style.top = Math.min(window.innerHeight - m.offsetHeight - 8, r.bottom + 8) + "px";
    m.style.left = Math.max(8, Math.min(window.innerWidth - w - 8, r.right - w)) + "px";
    menuEl = m;
    menuAnchor = anchor;
    anchor.setAttribute("aria-expanded", "true");
    const first = m.querySelector('[aria-checked="true"]') || m.querySelector("button:not([disabled])");
    if (first) first.focus();
  }
  document.addEventListener("mousedown", (e) => {
    if (menuEl && !menuEl.contains(e.target) && !(menuAnchor && menuAnchor.contains(e.target))) closeMenu(false);
  });
  document.addEventListener("keydown", (e) => {
    if (!menuEl) return;
    const btns = [...menuEl.querySelectorAll("button:not([disabled])")];
    const i = btns.indexOf(document.activeElement);
    if (e.key === "Escape") { e.preventDefault(); closeMenu(); }
    else if (e.key === "ArrowDown") { e.preventDefault(); btns[(i + 1) % btns.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); btns[(i - 1 + btns.length) % btns.length].focus(); }
    else if (e.key === "Home") { e.preventDefault(); btns[0].focus(); }
    else if (e.key === "End") { e.preventDefault(); btns[btns.length - 1].focus(); }
    else if (e.key === "Tab") closeMenu(false);
  });
  window.addEventListener("resize", () => closeMenu(false));

  // menu pengguna
  $("userBtn").addEventListener("click", () => {
    openMenu($("userBtn"), [
      { header: true, avatar: initial(me.username), avatarId: me.id, title: me.username, sub: `${t(isAdmin() ? "roleAdmin" : "roleUser")} · ${tn("acctCount", accounts.length)}` },
      { sep: true },
      { label: t("reload"), icon: "i-refresh", onClick: reloadAll },
      { label: t("changePassword"), icon: "i-key", onClick: () => setTimeout(openPwModal, 0) },
      ...(isAdmin() ? [{ label: t("manageUsers"), icon: "i-people", onClick: goUsers }] : []),
      { sep: true },
      { label: t("signOut"), icon: "i-exit", danger: true, onClick: logout },
    ], me.username, { className: "user-menu" });
  });

  async function reloadAll() {
    try {
      await Promise.all([loadSettings(), loadMyNotif(), loadContacts(), loadHistory(), loadSlots(), isAdmin() ? Promise.all([loadUsers(), loadQueueAdmin()]) : Promise.resolve()]);
      dashSig = "";
      await refresh();
    } catch (e) { toast(e.message); }
  }
  function goUsers() {
    showTab("settings");
    const h = $("usersHeading");
    setTimeout(() => { h.scrollIntoView({ behavior: "smooth", block: "start" }); h.focus({ preventScroll: true }); }, 50);
  }

  // modal ganti password
  let pwTrigger = null;
  function updateEyes() {
    document.querySelectorAll(".eye").forEach((b) => {
      const shown = $(b.dataset.eye).type === "text";
      b.setAttribute("aria-pressed", String(shown));
      b.setAttribute("aria-label", t(shown ? "hidePassword" : "showPassword"));
      b.title = b.getAttribute("aria-label");
      b.querySelector("use").setAttribute("href", shown ? "#i-eye-off" : "#i-eye");
    });
  }
  function openPwModal() {
    closeMenu(false);
    pwTrigger = document.activeElement && document.activeElement !== document.body ? document.activeElement : $("userBtn");
    $("pwForm").reset();
    ["pwCur", "pwNew", "pwConf"].forEach((id) => { $(id).type = "password"; });
    $("pwErr").textContent = "";
    $("pwSave").disabled = false;
    updateEyes();
    $("pwModal").classList.remove("hidden");
    document.body.style.overflow = "hidden";
    $("pwCur").focus();
  }
  function closePwModal(silent) {
    if ($("pwModal").classList.contains("hidden")) return;
    $("pwModal").classList.add("hidden");
    document.body.style.overflow = "";
    $("pwForm").reset();
    if (!silent && pwTrigger) pwTrigger.focus();
  }
  document.querySelectorAll(".eye").forEach((b) => b.addEventListener("click", () => {
    const inp = $(b.dataset.eye);
    inp.type = inp.type === "password" ? "text" : "password";
    updateEyes();
  }));
  $("pwCancel").addEventListener("click", () => closePwModal());
  $("pwModal").addEventListener("mousedown", (e) => { if (e.target === $("pwModal")) closePwModal(); });
  document.addEventListener("keydown", (e) => {
    const modal = [$("pwModal"), $("setSheet")].find((m) => !m.classList.contains("hidden"));
    if (!modal) return;
    if (e.key === "Escape") { e.preventDefault(); if (modal === $("pwModal")) closePwModal(); else closeSetSheet(); }
    else if (e.key === "Tab") {
      const f = [...modal.querySelectorAll("button:not([disabled]), input")].filter((x) => x.offsetParent !== null);
      const first = f[0], last = f[f.length - 1];
      if (!modal.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
      else if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  $("pwForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = $("pwErr");
    err.textContent = "";
    const cur = $("pwCur").value, nw = $("pwNew").value, cf = $("pwConf").value;
    if (!cur || !nw || !cf) { err.textContent = t("pwRequired"); return; }
    if (nw.length < 8) { err.textContent = t("pwTooShort"); $("pwNew").focus(); return; }
    if (nw !== cf) { err.textContent = t("passMismatch"); $("pwConf").focus(); return; }
    $("pwSave").disabled = true;
    try {
      await api("/auth/password", { method: "POST", body: { current: cur, new: nw } });
      closePwModal();
      toast(t("pwChanged"));
    } catch (ex) { err.textContent = ex.message; $("pwSave").disabled = false; }
  });

  // ------------------------------------------------------------------- tabs
  function showTab(tab) {
    document.querySelectorAll("#tabs button").forEach((b) => {
      const on = b.dataset.tab === tab;
      b.classList.toggle("active", on);
      if (on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    document.querySelectorAll("main > section").forEach((s) => s.classList.toggle("hidden", s.id !== "tab-" + tab));
    window.scrollTo({ top: 0 });
  }
  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("[data-tab]");
    if (b) showTab(b.dataset.tab);
  });
  document.querySelectorAll("[data-goto]").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    showTab(a.dataset.goto);
  }));

  // ---------------------------------------------------------------- accounts
  // Sinkronkan daftar akun dari server; return true bila akun terpilih berubah
  function syncAccounts(list) {
    accounts = list;
    let changed = false;
    if (accounts.length && !accounts.find((a) => a.id === currentId)) {
      currentId = accounts[0].id;
      changed = true;
      try { localStorage.setItem(ACCT_KEY, currentId); } catch (e) { /* abaikan */ }
    }
    const name = accounts.length ? curAccount().name : "-";
    $("acctAvatar").textContent = (name.trim()[0] || "?").toUpperCase();
    paint($("acctAvatar"), currentId);
    document.querySelectorAll(".acct-chip").forEach((c) => c.style.setProperty("--dot", avColor(currentId)[0]));
    $("acctBtnName").textContent = name;
    $("acctBtn").title = name;
    document.querySelectorAll(".acct-name-text").forEach((n) => { n.textContent = name; });
    setText("accountsCount", String(accounts.length));
    renderAccountList();
    return changed;
  }

  async function switchAccount(id) {
    currentId = id;
    try { localStorage.setItem(ACCT_KEY, id); } catch (e) { /* abaikan */ }
    if (loginTimer || loginMode !== "idle") { await api("/login/stop", { method: "POST" }).catch(() => {}); endLogin(null); }
    syncAccounts(accounts);
    dashSig = "";
    dash = null;
    await Promise.all([loadContacts(), loadDash()]);
    renderSchedules(curAccount().schedules);
    await refresh();
    renderDashboard(true);
  }

  const cookieDot = (c) => (c.invalid ? "bad" : c.present ? "ok" : "");
  const initial = (n) => (n.trim()[0] || "?").toUpperCase();

  $("acctBtn").addEventListener("click", () => {
    const items = accounts.map((a) => ({
      label: a.name, role: "menuitemradio", checked: a.id === currentId, avatar: initial(a.name), avatarId: a.id, dot: cookieDot(a.cookies),
      onClick: () => { if (a.id !== currentId) switchAccount(a.id); },
    }));
    items.push({ sep: true }, { label: t("manageAccounts"), onClick: () => showTab("accounts") });
    openMenu($("acctBtn"), items, t("activeAccount"));
  });

  function cookieBrief(c) {
    return t(c.invalid ? "cookieBriefBad" : !c.present ? "cookieBriefNone" : c.last_ok ? "cookieBriefOk" : "cookieBriefSaved");
  }

  // statistik antrean untuk admin (hanya hitungan)
  let queueAdmin = null;
  async function loadQueueAdmin() {
    if (!isAdmin()) return;
    try { queueAdmin = await api("/queue/admin"); renderQueueAdmin(); } catch (e) { /* abaikan */ }
  }
  function renderQueueAdmin() {
    const box = $("queueAdminList");
    if (!box || !queueAdmin) return;
    box.replaceChildren();
    const row = (label, val, id) => el("div", { className: "nav-row static", ...(id ? { id } : {}) }, [el("span", { className: "nr-label", textContent: label }), el("span", { className: "nr-val", textContent: val })]);
    box.append(row(t("qWorkers"), String(queueAdmin.workers)), row(t("qQueued"), String(queueAdmin.queued)), row(t("qRunning"), String(queueAdmin.running)),
      row(t("qLogin"), `${queueAdmin.login_sessions}/${queueAdmin.login_limit}`));
    const load = Object.entries(queueAdmin.load_by_hour || {});
    const max = Math.max(1, ...load.map(([, n]) => n));
    const bars = el("div", { className: "load-bars", role: "img", "aria-label": t("qLoad") });
    if (!load.length) bars.append(el("span", { className: "muted", textContent: t("qNoLoad") }));
    load.forEach(([h, n]) => bars.append(el("div", { className: "lb-col", title: `${h} · ${n}` }, [el("span", { className: "lb-bar", style: `height:${6 + Math.round((n / max) * 40)}px` }),
      el("span", { className: "lb-n", textContent: String(n) }), el("span", { className: "lb-h", textContent: h.slice(0, 2) })])));
    box.append(el("div", { className: "nav-row static col" }, [el("span", { className: "nr-label", textContent: t("qLoad") }), bars]));
  }

  // kepadatan jadwal per slot 30 menit (untuk petunjuk di editor jadwal)
  let slotInfo = null;
  async function loadSlots() {
    try { slotInfo = await api("/queue/slots"); } catch (e) { slotInfo = null; }
    document.querySelectorAll(".sched").forEach((r) => r.updateHint && r.updateHint());
  }
  const slotKey = (hh, mm) => `${hh}:${+mm >= 30 ? "30" : "00"}`;

  async function loadUsers() {
    users = (await api("/users")).users;
    renderUsers();
  }

  function renderAccountList(force) {
    const sig = JSON.stringify([lang, currentId, accounts]);
    if (!force && renderAccountList.sig === sig) return;
    renderAccountList.sig = sig;
    const box = $("accountList");
    box.replaceChildren();
    accounts.forEach((a) => {
      const on = a.id === currentId;
      const lastOne = accounts.length < 2;
      const more = el("button", { className: "more-btn", type: "button", "aria-haspopup": "menu", "aria-expanded": "false", "aria-label": `${t("moreActions")}: ${a.name}` }, [icon("i-more")]);
      more.addEventListener("click", () => {
        const items = [
          { label: on ? t("picked") : t("pick"), disabled: on, onClick: () => switchAccount(a.id) },
          { label: t("rename"), onClick: async () => {
            const name = prompt(t("promptAccountName"), a.name);
            if (!name || name.trim() === a.name) return;
            try { await api("/accounts/" + a.id, { method: "PUT", body: { name } }); await refresh(); }
            catch (e) { toast(e.message); }
          } },
        ];
        items.push({ sep: true }, { label: t("del"), danger: true, disabled: lastOne, reason: lastOne ? t("lastAccount") : "", onClick: async () => {
          if (!confirm(t("confirmDeleteAccount", { name: a.name }))) return;
          try { await api("/accounts/" + a.id, { method: "DELETE" }); await refresh(); }
          catch (e) { toast(e.message); }
        } });
        openMenu(more, items, a.name);
      });
      const meta = t("acctMeta", { contacts: tn("nContacts", a.contacts), cookie: cookieBrief(a.cookies), next: a.next ? a.next.time : t("noNext") });
      const titleLine = el("div", { className: "title-line" }, [el("span", { className: "title", textContent: a.name })]);
      if (on) titleLine.append(el("span", { className: "badge accent", textContent: t("activeBadge") }));
      const info = [titleLine, el("div", { className: "meta line", textContent: meta })];
      box.append(el("div", { className: on ? "current" : "" }, [
        paint(el("span", { className: "avatar-sm", textContent: initial(a.name), "aria-hidden": "true" }), a.id),
        el("div", { className: "grow" }, info),
        more,
      ]));
    });
  }

  $("btnAddAccount").addEventListener("click", async () => {
    $("accountErr").textContent = "";
    try {
      const acc = await api("/accounts", { method: "POST", body: { name: $("newAccountName").value } });
      $("newAccountName").value = "";
      st = await api("/status");
      serverNow = st.server_now || serverNow;
      syncAccounts(st.accounts);
      await switchAccount(acc.id);
      toast(t("toastAccountCreated", { name: acc.name }));
    } catch (e) { $("accountErr").textContent = e.message; }
  });

  // -------------------------------------------------------------- dashboard
  const slotsOfToday = (a) => a.schedules.filter((s) => s.enabled).sort((x, y) => x.time.localeCompare(y.time));
  const expectedCount = (a, s) => (s.contacts == null ? a.contacts : s.contacts.length);
  const recipText = (a, contacts) => (contacts == null ? t("allContacts", { n: a.contacts }) : tn("nContacts", contacts.length));

  function ringState(a) {
    const n = a.next;
    const fg = $("ringFg");
    if (!n) {
      fg.setAttribute("stroke-dashoffset", "377");
      setText("ringText", "--");
      $("ringSvg").setAttribute("aria-label", t("ringNone"));
      return;
    }
    const rem = Math.max(0, n.epoch - Date.now() / 1000);
    const progress = clamp(1 - rem / 86400, 0, 1);
    fg.setAttribute("stroke-dashoffset", String(377 * (1 - progress)));
    const txt = `${Math.floor(rem / 3600)}:${pad(Math.floor((rem % 3600) / 60))}`;
    setText("ringText", txt);
    $("ringSvg").setAttribute("aria-label", t("ringAria", { time: txt }));
  }

  function renderDashboard(force) {
    if (!st || !accounts.length) return;
    const a = curAccount();
    ringState(a);
    const sig = JSON.stringify([lang, currentId, accounts, st.running, st.queue, st.current && [st.current.id, st.current.status, st.current.sent, (st.current.results || []).length],
      serverNow.slice(0, 16), dash, settings, contactList]);
    if (!force && sig === dashSig) return;
    dashSig = sig;

    const today = dayOf(serverNow);
    const nowHm = hhmmOf(serverNow);
    setText("dashDate", titleCase(new Intl.DateTimeFormat(LOCALE[lang], { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }).format(dayDate(today))));

    // pil antrean
    const pill = $("queuePill");
    const waiting = ((st.queue && st.queue.mine) || []).some((j) => j.state === "queued");
    pill.className = "pill " + (st.running || waiting ? "busy" : "ok");
    pill.textContent = st.running ? (st.current && st.current.account ? t("busyAcct", { name: st.current.account.name }) : t("busy")) : waiting ? t("queued") : t("ready");

    // jadwal berikutnya
    const n = a.next;
    const defMsg = settings ? settings.message : "";
    if (!n) {
      setText("heroTime", "--:--");
      setText("heroSlot", t("noSchedule"));
      setText("heroMeta", t("noScheduleHint"));
      $("heroMeta").classList.remove("hidden");
    } else {
      setText("heroTime", n.time);
      setText("heroSlot", `${slotPart(n.time)} · ${recipText(a, n.contacts)}`);
      const hm = $("heroMeta");
      hm.replaceChildren();
      hm.classList.toggle("hidden", !n.message);
      if (n.message) hm.append(el("span", { textContent: t("pesanLabel") + " " }), el("strong", { className: "msg-q", textContent: `"${n.message}"` }));
    }

    // data hari ini
    const mine = dash ? dash.runs_today : [];
    const cur = st.running && st.current && st.current.account && st.current.account.id === currentId ? st.current : null;
    const sendRuns = (cur && cur.mode === "send" ? [cur] : []).concat(mine);
    const slots = slotsOfToday(a);
    const isDone = (r) => r.status === "success" || r.status === "partial";
    const todaySlots = slots.map((s) => {
      const cands = sendRuns.filter((r) => r.label === s.time && r.trigger === "schedule" && dayOf(r.started_at) === today);
      const run = cands.find(isDone) || cands.find((r) => r.status === "running") || cands[0] || null;
      const status = run ? run.status : s.time < nowHm ? "missed" : "pending";
      return { s, run, status, done: !!run && isDone(run) };
    });

    renderStreak(today);
    renderGoal(a, todaySlots);
    renderWeek(today, todaySlots, slots.length);
    renderStatusWidgets(a);
    renderTodayList(a, todaySlots);
    renderCookieBanner(a.cookies);
    renderHistory();
  }

  function renderStreak(today) {
    const days = new Set(dash ? dash.send_days : []);
    let day = days.has(today) ? today : addDays(today, -1);
    let n = 0;
    while (days.has(day)) { n++; day = addDays(day, -1); }
    setText("streakNum", String(n));
  }

  function renderGoal(a, todaySlots) {
    const total = todaySlots.length;
    const done = todaySlots.filter((x) => x.done).length;
    let sent = 0, targeted = 0;
    todaySlots.forEach((x) => {
      sent += x.run ? x.run.sent || 0 : 0;
      targeted += x.done ? x.run.total : expectedCount(a, x.s);
    });
    setText("goalSched", `${done}/${total}`);
    setText("goalContacts", `${sent}/${targeted}`);
    $("goalFg").setAttribute("stroke-dashoffset", String(351.9 * (1 - (total ? done / total : 0))));
  }

  function renderWeek(today, todaySlots, scheduleCount) {
    const box = $("weekDays");
    box.replaceChildren();
    let good = 0;
    const fmt = new Intl.DateTimeFormat(LOCALE[lang], { weekday: "short", timeZone: "UTC" });
    for (let i = 6; i >= 0; i--) {
      const day = addDays(today, -i);
      const isToday = i === 0;
      const ds = dash && dash.week ? dash.week[day] : null;
      let state, style = "";
      const pending = isToday && scheduleCount > 0 && todaySlots.some((x) => !x.done);
      if (pending) {
        state = "ring-day";
        style = `${Math.round((todaySlots.filter((x) => x.done).length / scheduleCount) * 100)}%`;
      } else if (ds && ds.runs) {
        state = ds.sent <= 0 ? "failed" : ds.full >= ds.runs ? "success" : "partial";
      } else {
        state = scheduleCount === 0 ? "rest" : "none";
      }
      if (state === "success") good++;
      const dot = el("span", { className: "dot " + state });
      if (style) dot.style.setProperty("--p", style);
      if (state === "success") dot.append(icon("i-check"));
      else if (state === "partial") dot.append(icon("i-bang"));
      else if (state === "failed") dot.append(icon("i-x"));
      else if (state === "rest") dot.textContent = "zz";
      box.append(el("div", { className: "day" + (isToday ? " today" : "") }, [dot, el("span", { className: "lbl", textContent: titleCase(fmt.format(dayDate(day))) })]));
    }
    setText("weekGood", `${good}/7`);
    setText("weekLbl", " " + t("goodDays"));
  }

  // saluran notifikasi aktif milik pengguna ini (+ global bila admin)
  function activeChannels() {
    const on = { Discord: false, Telegram: false };
    if (myNotif) {
      on.Discord = on.Discord || (myNotif.discord_enabled && myNotif.discord_webhook_set);
      on.Telegram = on.Telegram || (myNotif.telegram_enabled && myNotif.telegram_token_set && !!myNotif.telegram_chat_id);
    }
    if (isAdmin() && settings) {
      on.Discord = on.Discord || (settings.discord_enabled && settings.discord_webhook_set);
      on.Telegram = on.Telegram || (settings.telegram_enabled && settings.telegram_token_set && !!settings.telegram_chat_id);
    }
    return on;
  }
  const globalChannelNames = () => {
    const n = [];
    if (settings && settings.discord_enabled && settings.discord_webhook_set) n.push("Discord");
    if (settings && settings.telegram_enabled && settings.telegram_token_set && settings.telegram_chat_id) n.push("Telegram");
    return n.length ? n.join(" & ") : t("notifOff");
  };

  function renderStatusWidgets(a) {
    const c = a.cookies;
    $("cookieIcon").className = "w-icon " + (c.invalid ? "red" : !c.present ? "" : "green");
    setText("cookieValue", t(c.invalid ? "cookieInvalid" : !c.present ? "cookieUnset" : "cookieValid"));
    setText("cookieSub", c.invalid ? c.invalid : !c.present ? t("cookieNotSet") : c.last_ok ? t("checkedAgo", { when: relTime(c.last_ok) }) : t("notVerified"));
    if (settings) {
      const ka = settings.keepalive_enabled;
      setText("refreshValue", ka ? tn("refreshEvery", settings.keepalive_hours) : t("refreshOff"));
      setText("refreshSub", ka ? (a.keepalive_next ? t("nextAt", { time: a.keepalive_next }) : t("refreshOn")) : t("refreshOffSub"));
    }
    const on = activeChannels();
    const names = Object.keys(on).filter((k) => on[k]);
    setText("notifValue", names.length ? names.join(" & ") : t("notifOff"));
    setText("notifSub", names.length === 2 ? t("bothActive") : names.length === 1 ? t("chOff", { name: names[0] === "Discord" ? "Telegram" : "Discord" }) : t("allOff"));
    setText("accountsValue", tn("nAccounts", accounts.length));
    setText("accountsSub", t("totalContacts", { n: accounts.reduce((x, y) => x + y.contacts, 0) }));
  }

  function evidenceText(ev) {
    if (!ev) return "";
    const p = [];
    if (ev.chat) p.push(t("evChat"));
    if (ev.bubble) p.push(t("evBubble"));
    if (ev.list_time) p.push(t("evList", { time: ev.list_time }));
    if (ev.renamed_to) p.push(t("evRenamed", { name: ev.renamed_to }));
    return p.join(" · ");
  }

  function contactRow(name, res) {
    const ok = res && res.ok;
    const fail = res && !res.ok;
    const dot = el("span", { className: "sdot" + (ok ? " success" : fail ? " failed" : "") });
    if (ok) dot.append(icon("i-check")); else if (fail) dot.append(icon("i-x"));
    let detail = "";
    if (ok) detail = evidenceText(res.evidence);
    else if (fail) detail = res.error || "";
    if (!res) detail = t("notSent");
    const time = res && res.sent_at ? res.sent_at.slice(0, 8) : "—";
    return el("div", { className: "crow" + (res ? "" : " pend") }, [dot, el("span", { className: "name", textContent: name }),
      el("span", { className: "detail", textContent: detail }), el("span", { className: "time", textContent: time })]);
  }

  function renderTodayList(a, todaySlots) {
    const box = $("todayList");
    box.replaceChildren();
    setText("todayCount", tn("nSchedules", todaySlots.length));
    if (!todaySlots.length) {
      box.append(el("p", { className: "empty", textContent: t("emptyToday") }));
      return;
    }
    todaySlots.forEach(({ s, run, status }) => {
      const head = el("div", { className: "slot-head" }, [
        el("div", {}, [el("span", { className: "slot-time", textContent: s.time }),
          el("span", { className: "muted", textContent: `${slotPart(s.time)} · ${recipText(a, s.contacts)}` })]),
        status === "success" && run ? badge(status, t("doneSlot", { s: run.sent, t: run.total })) : badge(status),
      ]);
      const slot = el("div", { className: "slot" }, [head]);
      const names = s.contacts == null ? contactList : s.contacts;
      const results = run ? run.results || [] : [];
      const seen = new Set();
      results.forEach((r) => { seen.add(r.contact.toLowerCase()); slot.append(contactRow(r.contact, r)); });
      names.filter((c) => !seen.has(c.toLowerCase())).forEach((c) => slot.append(contactRow(c, null)));
      box.append(slot);
    });
  }

  // ------------------------------------------------------------ log & history
  async function refresh() {
    try {
      const [s, cur] = await Promise.all([api("/status"), api("/run/current?since=" + logCursor)]);
      st = s;
      serverNow = s.server_now || serverNow;
      if (syncAccounts(s.accounts)) { await switchAccount(currentId); return; }
      renderDashboard();
      renderQueue();

      if (cur.run) {
        if (cur.run.id !== lastRunId) {
          lastRunId = cur.run.id;
          logCursor = 0;
          pinned = false;
          $("logBox").textContent = "";
          idleLogKey = null;
          return refresh();
        }
        if (!pinned) {
          appendLogs(cur.logs);
          setRunBadge(cur.run.status);
        }
        logCursor = cur.next;
        if (!s.running && wasRunning) await loadHistory();
      } else renderIdleLog();
      wasRunning = s.running;
    } catch (e) { /* 401 ditangani di api() */ }
  }

  // Tanpa proses berjalan: tampilkan log proses terakhir dari riwayat (atau keterangan kosong)
  let idleLogKey = null;
  function renderIdleLog() {
    if (pinned || lastRunId) return;
    const last = st && st.last_run;
    const key = last ? last.id + last.status + (last.logs || []).length : "none:" + lang;
    if (key === idleLogKey) return;
    idleLogKey = key;
    const box = $("logBox");
    box.replaceChildren();
    if (last) {
      (last.logs || []).forEach((l) => box.append(logLine(l)));
      setRunBadge(last.status);
      box.scrollTop = box.scrollHeight;
    } else {
      box.append(el("div", { className: "log-empty", textContent: t("noRuns") }));
      setRunBadge("");
    }
  }

  function setRunBadge(status) {
    const b = $("runBadge");
    b.className = "badge " + status;
    b.textContent = status ? statusLabel(status) : "";
    b.dataset.status = status || "";
  }

  function logLine(l) { return el("div", { className: l.level, textContent: `[${l.t}] ${l.msg}` }); }
  function appendLogs(lines) {
    if (!lines.length) return;
    const box = $("logBox");
    const atBottom = box.scrollTop + box.clientHeight >= box.scrollHeight - 20;
    lines.forEach((l) => box.append(logLine(l)));
    if (atBottom) box.scrollTop = box.scrollHeight;
  }

  // ---- antrean: job milik pengguna untuk akun terpilih (dasbor = kirim/uji, tab cookie = cek)
  let queueSig = "";
  const myJobs = (check) => ((st && st.queue && st.queue.mine) || []).filter((j) => j.account_id === currentId && (j.kind === "check") === check);
  function queueLine(j) {
    if (j.state === "running") return t("runningState");
    const parts = [t("queued"), t("queuePos", { n: j.position })];
    if (j.eta) parts.push(t("queueEta", { time: j.eta }));
    return parts.join(" · ");
  }
  function fillQueueBox(box, jobsList) {
    box.replaceChildren();
    box.classList.toggle("hidden", !jobsList.length);
    jobsList.forEach((j) => {
      const row = el("div", { className: "qrow " + j.state }, [el("span", { className: "qdot" }), el("span", { className: "qtext", textContent: queueLine(j) })]);
      if (j.state === "queued") {
        const b = el("button", { type: "button", className: "btn plain small destructive-text", textContent: t("cancelJob") });
        b.addEventListener("click", async () => {
          b.disabled = true;
          try { await api("/jobs/" + encodeURIComponent(j.id), { method: "DELETE" }); toast(t("toastJobCancelled")); } catch (e) { toast(e.message); }
          await refresh();
        });
        row.append(b);
      }
      box.append(row);
    });
  }
  function renderQueue(force) {
    if (!st) return;
    const sig = JSON.stringify([lang, currentId, st.queue, st.running]);
    if (!force && sig === queueSig) return;
    queueSig = sig;
    const dj = myJobs(false), cj = myJobs(true);
    fillQueueBox($("queueBox"), dj);
    fillQueueBox($("cookieQueue"), cj);
    const busy = dj.length > 0;
    $("btnSend").disabled = $("btnTest").disabled = busy;
    $("btnStop").classList.toggle("hidden", !dj.some((j) => j.state === "running"));
    $("btnCheckCookies").disabled = cj.length > 0;
  }

  async function startRun(mode) {
    $("runErr").textContent = "";
    try {
      await api("/run", { method: "POST", body: { mode, account: currentId, message: $("runMessage").value.trim() || null } });
      await refresh();
    } catch (e) { $("runErr").textContent = e.message; }
  }
  $("btnSend").addEventListener("click", () => {
    if (confirm(t("confirmSend", { name: curAccount().name }))) startRun("send");
  });
  $("btnTest").addEventListener("click", () => startRun("test"));
  $("btnStop").addEventListener("click", () => api("/run/stop?account=" + encodeURIComponent(currentId), { method: "POST" }).then(() => toast(t("toastStopping"))).catch((e) => toast(e.message)));

  // ------------------------------------------------------------- lightbox
  const lb = { items: [], index: 0, trigger: null, open: false };
  function buildLightbox() {
    const caption = el("span", { className: "lb-caption" });
    const dl = el("a", { className: "lb-btn", id: "lbDownload" });
    const close = el("button", { className: "lb-btn lb-close", type: "button", id: "lbClose" }, [icon("i-x")]);
    const prev = el("button", { className: "lb-nav prev", type: "button", id: "lbPrev" }, [icon("i-chev")]);
    const next = el("button", { className: "lb-nav next", type: "button", id: "lbNext" }, [icon("i-chev")]);
    const img = el("img", { id: "lbImg", draggable: false, alt: "" });
    const stage = el("div", { className: "lb-stage" }, [img]);
    const root = el("div", { id: "lightbox", className: "lightbox hidden", role: "dialog", "aria-modal": "true" }, [
      el("div", { className: "lb-bar" }, [caption, dl, close]), prev, next, stage]);
    document.body.append(root);
    root.addEventListener("click", (e) => { if (e.target === root || e.target === stage) closeLightbox(); });
    close.addEventListener("click", closeLightbox);
    prev.addEventListener("click", () => stepLightbox(-1));
    next.addEventListener("click", () => stepLightbox(1));
    img.addEventListener("click", () => { stage.classList.toggle("zoom"); updateZoomHint(); });
    return root;
  }
  const lightboxEl = buildLightbox();

  function updateZoomHint() {
    const zoomed = lightboxEl.querySelector(".lb-stage").classList.contains("zoom");
    $("lbImg").title = t(zoomed ? "lbZoomOut" : "lbZoomIn");
  }
  function showLightboxItem() {
    const it = lb.items[lb.index];
    const n = lb.items.length;
    const cap = n > 1 ? `${it.caption} (${lb.index + 1}/${n})` : it.caption;
    lightboxEl.querySelector(".lb-caption").textContent = cap;
    lightboxEl.setAttribute("aria-label", cap);
    $("lbImg").src = it.url;
    $("lbImg").alt = it.caption;
    lightboxEl.querySelector(".lb-stage").classList.remove("zoom");
    lightboxEl.querySelector(".lb-stage").scrollTo(0, 0);
    updateZoomHint();
    const dl = $("lbDownload");
    dl.href = it.url;
    dl.download = it.filename;
    dl.textContent = t("lbDownload");
    $("lbClose").setAttribute("aria-label", t("lbClose"));
    $("lbClose").title = t("lbClose");
    $("lbPrev").setAttribute("aria-label", t("lbPrev"));
    $("lbNext").setAttribute("aria-label", t("lbNext"));
    $("lbPrev").classList.toggle("hidden", n < 2);
    $("lbNext").classList.toggle("hidden", n < 2);
  }
  function stepLightbox(d) {
    const n = lb.items.length;
    if (n < 2) return;
    lb.index = (lb.index + d + n) % n;
    showLightboxItem();
  }
  // items: [{url, caption, filename, revoke}]; trigger: elemen yang mendapat fokus kembali
  function openLightbox(items, index, trigger) {
    lb.items = items;
    lb.index = index || 0;
    lb.trigger = trigger || document.activeElement;
    lb.open = true;
    showLightboxItem();
    lightboxEl.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    $("lbClose").focus();
  }
  function closeLightbox() {
    if (!lb.open) return;
    lb.open = false;
    lightboxEl.classList.add("hidden");
    document.body.style.overflow = "";
    $("lbImg").removeAttribute("src");
    lb.items.forEach((it) => { if (it.revoke) URL.revokeObjectURL(it.url); });
    lb.items = [];
    if (lb.trigger && lb.trigger.focus) lb.trigger.focus();
  }
  document.addEventListener("keydown", (e) => {
    if (!lb.open) return;
    if (e.key === "Escape") { e.preventDefault(); closeLightbox(); }
    else if (e.key === "ArrowLeft") stepLightbox(-1);
    else if (e.key === "ArrowRight") stepLightbox(1);
    else if (e.key === "Tab") {
      const f = [...lightboxEl.querySelectorAll("a[href], button")].filter((x) => !x.classList.contains("hidden"));
      const first = f[0], last = f[f.length - 1];
      if (!lightboxEl.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
      else if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  // Pratinjau inline tangkapan layar terakhir; klik gambar atau tombol Layar Penuh membuka lightbox
  let shotUrl = null;
  function renderShotButtons() {
    $("btnShot").textContent = t(shotUrl ? "reloadScreenshot" : "viewScreenshot");
    $("btnShotFull").classList.toggle("hidden", !shotUrl);
  }
  function openShot(trigger) {
    if (!shotUrl) return;
    openLightbox([{ url: shotUrl, caption: t("lbLatestShot"), filename: "streak-screenshot.jpg" }], 0, trigger);
  }
  $("btnShot").addEventListener("click", async () => {
    try {
      const res = await fetch("/api/run/screenshot?t=" + Date.now(), { credentials: "same-origin" });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.status);
      const old = shotUrl;
      shotUrl = URL.createObjectURL(await res.blob());
      const img = $("shotView");
      img.src = shotUrl;
      img.alt = t("lbLatestShot");
      img.classList.remove("hidden");
      if (old) URL.revokeObjectURL(old);
      renderShotButtons();
    } catch (e) { toast(e.message); }
  });
  $("btnShotFull").addEventListener("click", () => openShot($("btnShotFull")));
  $("shotView").addEventListener("click", () => openShot($("shotView")));
  $("shotView").addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openShot($("shotView")); } });

  let proofUrls = [];
  let proofToken = 0;
  async function showProofs(run) {
    const box = $("proofBox");
    const token = ++proofToken;
    proofUrls.forEach((u) => URL.revokeObjectURL(u));
    proofUrls = [];
    box.replaceChildren();
    const items = [];
    for (const r of run.results || []) {
      if (!r.proof) continue;
      try {
        const res = await fetch(`/api/proof/${run.id}/${r.proof}`, { credentials: "same-origin" });
        if (!res.ok) continue;
        const blob = await res.blob();
        if (token !== proofToken) return;
        const url = URL.createObjectURL(blob);
        proofUrls.push(url);
        const cap = `${r.contact} ${r.sent_at || ""}`.trim();
        items.push({ url, caption: cap, filename: `${r.contact}-${run.id}-${r.proof}`.replace(/[^\w.-]+/g, "_") });
        const idx = items.length - 1;
        const img = el("img", { src: url, alt: t("proofAlt", { name: r.contact }) });
        const btn = el("button", { className: "proof-btn", type: "button", "aria-label": t("proofAlt", { name: r.contact }) }, [img]);
        btn.addEventListener("click", () => openLightbox(items, idx, btn));
        box.append(el("figure", {}, [btn, el("figcaption", { textContent: `${r.contact} — ${r.sent_at || ""}` })]));
      } catch (e) { /* abaikan */ }
    }
  }

  async function loadDash() {
    if (!currentId) { dash = null; return; }
    const id = currentId;
    try {
      const d = await api("/dashboard?account=" + encodeURIComponent(id));
      if (id === currentId) dash = d;
    } catch (e) { /* abaikan */ }
  }

  async function loadHistory() {
    const seq = ++histSeq;
    const q = new URLSearchParams({ account: "all", page: String(hf.page), page_size: String(hf.size) });
    if (hf.mode) q.set("mode", hf.mode);
    if (hf.status) q.set("status", hf.status);
    const [h] = await Promise.all([api("/history?" + q), loadDash()]);
    if (seq !== histSeq) return;
    const pages = Math.max(1, Math.ceil(h.total / h.page_size));
    if (h.page > pages) { hf.page = pages; saveHF(); return loadHistory(); }
    hist = h;
    renderIdleLog();
    renderHistory();
    renderDashboard(true);
  }

  // daftar nomor halaman ringkas: 1 … 4 5 6 … 12
  function pageItems(cur, pages) {
    const keep = [...new Set([1, pages, cur - 1, cur, cur + 1].filter((n) => n >= 1 && n <= pages))].sort((a, b) => a - b);
    const out = [];
    keep.forEach((n, i) => {
      if (i) {
        const gap = n - keep[i - 1];
        if (gap === 2) out.push(n - 1);
        else if (gap > 2) out.push("…");
      }
      out.push(n);
    });
    return out;
  }

  function goPage(n) {
    hf.page = n;
    saveHF();
    loadHistory().catch(() => {});
  }

  function renderPager() {
    const pages = Math.max(1, Math.ceil(hist.total / hist.page_size));
    const cur = Math.min(hist.page, pages);
    const from = hist.total ? (cur - 1) * hist.page_size + 1 : 0;
    const to = Math.min(hist.total, cur * hist.page_size);
    setText("pagerInfo", hist.total ? t("showing", { a: from, b: to, n: hist.total }) : t("showingNone"));
    $("pgPrev").disabled = cur <= 1;
    $("pgNext").disabled = cur >= pages;
    const box = $("pgNums");
    box.replaceChildren();
    pageItems(cur, pages).forEach((n) => {
      if (n === "…") { box.append(el("span", { className: "pg-gap", textContent: "…", "aria-hidden": "true" })); return; }
      const b = el("button", { type: "button", className: "pg-num" + (n === cur ? " on" : ""), textContent: String(n), "aria-label": t("pageN", { n }) });
      if (n === cur) b.setAttribute("aria-current", "page");
      b.addEventListener("click", () => { if (n !== cur) goPage(n); });
      box.append(b);
    });
    $("pager").classList.toggle("hidden", !hist.total && !hf.mode && !hf.status);
  }

  function renderHistFilters() {
    const seg = $("fMode");
    seg.replaceChildren();
    [["", "fAll"], ["send", "fSend"], ["check", "fCheck"]].forEach(([v, k]) => {
      const b = el("button", { type: "button", className: "fchip", textContent: t(k), "aria-pressed": String(hf.mode === v) });
      b.addEventListener("click", () => { if (hf.mode === v) return; hf.mode = v; hf.page = 1; saveHF(); renderHistFilters(); loadHistory().catch(() => {}); });
      seg.append(b);
    });
    seg.setAttribute("aria-label", t("filterMode"));
    const ss = $("fStatus");
    ss.replaceChildren(new Option(t("statusAll"), ""));
    ["success", "partial", "failed", "expired", "cancelled"].forEach((k) => ss.append(new Option(t("st_" + k), k)));
    ss.value = hf.status;
    ss.setAttribute("aria-label", t("filterStatus"));
    const sz = $("pgSize");
    sz.replaceChildren();
    [10, 20, 50].forEach((n) => sz.append(new Option(t("perPage", { n }), String(n))));
    sz.value = String(hf.size);
    sz.setAttribute("aria-label", t("pageSizeLbl"));
    $("pgPrev").setAttribute("aria-label", t("prevPage"));
    $("pgNext").setAttribute("aria-label", t("nextPage"));
    $("pager").setAttribute("aria-label", t("pagination"));
  }
  $("fStatus").addEventListener("change", (e) => { hf.status = e.target.value; hf.page = 1; saveHF(); loadHistory().catch(() => {}); });
  $("pgSize").addEventListener("change", (e) => { hf.size = +e.target.value; hf.page = 1; saveHF(); loadHistory().catch(() => {}); });
  $("pgPrev").addEventListener("click", () => goPage(Math.max(1, hist.page - 1)));
  $("pgNext").addEventListener("click", () => goPage(hist.page + 1));

  function renderHistory() {
    const body = $("historyBody");
    body.replaceChildren();
    renderPager();
    if (!hist.items.length) {
      body.append(el("tr", { className: "empty-row" }, [el("td", { colSpan: 6, className: "muted", textContent: t(hist.total || hf.mode || hf.status ? "noHistoryFiltered" : "noHistory") })]));
      return;
    }
    hist.items.forEach((r) => {
      const type = { test: t("typeTest"), check: t("typeCheck") }[r.mode] || t("typeSend");
      const how = r.trigger === "schedule" ? r.label || "" : r.trigger === "keepalive" ? t("trAuto") : [t("trManual"), r.by].filter(Boolean).join(" · ");
      const tr = el("tr", { tabIndex: 0, title: t("clickForLog") }, [
        el("td", { className: "h-time", textContent: fmtDateTime(r.started_at) }),
        el("td", { className: "h-acct", textContent: (r.account && r.account.name) || "-" }),
        el("td", { className: "h-type", textContent: how ? `${type} · ${how}` : type }),
        el("td", { className: "num h-res", textContent: r.mode === "check" ? "-" : `${r.sent}/${r.total}` }),
        el("td", { className: "num h-dur", textContent: duration(r) }),
        el("td", { className: "h-st" }, [badge(r.status)]),
      ]);
      const open = () => {
        const box = $("logBox");
        box.replaceChildren();
        (r.logs || []).forEach((l) => box.append(logLine(l)));
        pinned = true;
        setRunBadge(r.status);
        showProofs(r);
        $("logBox").scrollIntoView({ behavior: "smooth", block: "center" });
      };
      tr.addEventListener("click", open);
      tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
      body.append(tr);
    });
  }
  $("clearHistory").addEventListener("click", async () => {
    if (!confirm(t("confirmClear"))) return;
    try { await api("/history", { method: "DELETE" }); hf.page = 1; saveHF(); await loadHistory(); await refresh(); } catch (e) { toast(e.message); }
  });

  // --------------------------------------------------------------- contacts
  async function loadContacts() {
    const { contacts } = await apiA("/contacts");
    renderContacts(contacts);
  }
  function renderContacts(contacts) {
    contactList = contacts;
    document.querySelectorAll(".sched").forEach((r) => r.setContacts && r.setContacts());
    setText("contactsCount", String(contacts.length));
    const ul = $("contactsList");
    ul.replaceChildren();
    if (!contacts.length) ul.append(el("li", { className: "muted", textContent: t("noContacts") }));
    contacts.forEach((c) => {
      const more = el("button", { className: "more-btn", type: "button", "aria-haspopup": "menu", "aria-expanded": "false", "aria-label": `${t("moreActions")}: ${c}` }, [icon("i-more")]);
      more.addEventListener("click", () => openMenu(more, [
        { label: t("rename"), icon: "i-pencil", onClick: async () => {
          const name = prompt(t("promptRename"), c);
          if (!name || name.trim() === c) return;
          try {
            renderContacts((await apiA("/contacts/rename", { method: "PUT", body: { old: c, new: name } })).contacts);
            await refresh();
            renderSchedules(curAccount().schedules);
          } catch (e) { toast(e.message); }
        } },
        { sep: true },
        { label: t("delContact"), icon: "i-trash", danger: true, onClick: async () => {
          try { renderContacts((await apiA("/contacts?name=" + encodeURIComponent(c), { method: "DELETE" })).contacts); await refresh(); }
          catch (e) { toast(e.message); }
        } },
      ], c));
      ul.append(el("li", {}, [el("div", { className: "grow" }, [el("div", { className: "title", textContent: c })]), more]));
    });
    dashSig = "";
    renderDashboard();
  }
  $("btnAddContacts").addEventListener("click", async () => {
    $("contactsErr").textContent = "";
    try {
      const r = await apiA("/contacts", { method: "POST", body: { names: $("contactsInput").value } });
      $("contactsInput").value = "";
      renderContacts(r.contacts);
      await refresh();
      toast(t("toastAdded", { n: r.added.length }));
    } catch (e) { $("contactsErr").textContent = e.message; }
  });

  // ---------------------------------------------------------------- cookies
  function renderCookieBanner(c) {
    const box = $("cookieBanner");
    const kind = c.invalid ? "bad" : !c.present ? "none" : "ok";
    box.className = "banner " + kind;
    if (kind !== lastCookieKind) {
      lastCookieKind = kind;
      if (kind !== "ok" && !manualTouched) $("manualCookie").open = true;
    }
    let title, sub;
    if (kind === "bad") { title = t("bannerBad"); sub = c.invalid; }
    else if (kind === "none") { title = t("bannerNone"); sub = t("bannerNoneSub"); }
    else {
      title = t("bannerOk");
      const p = [t("cookieCount", { n: c.count }), c.last_ok ? t("checkedAgo", { when: relTime(c.last_ok) }) : t("notVerified")];
      if (c.last_saved) p.push(t("savedAgo", { when: relTime(c.last_saved) }));
      if (!c.has_session) p.push(t("warnNoSession"));
      sub = p.join(" · ");
    }
    box.replaceChildren(
      el("span", { className: "b-icon" }, [icon(kind === "ok" ? "i-check" : kind === "bad" ? "i-x" : "i-key")]),
      el("span", {}, [el("span", { className: "b-title", textContent: title }), el("br"), el("span", { className: "b-sub", textContent: sub })]),
    );
  }

  $("btnCheckCookies").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      await api("/run", { method: "POST", body: { mode: "check", account: currentId } });
      toast(t("toastChecking"));
      await refresh();
    } catch (e) { $("cookieErr").textContent = e.message; }
  });
  // Validasi cookie di sisi klien (mengikuti parser server); nilai cookie tidak pernah ditampilkan
  function parseCookieText(raw) {
    raw = (raw || "").trim();
    if (!raw) return null;
    let items = [];
    if ("[{".includes(raw[0])) {
      let data;
      try { data = JSON.parse(raw); } catch (e) { return { bad: true }; }
      if (data && !Array.isArray(data) && typeof data === "object") data = Array.isArray(data.cookies) ? data.cookies : [data];
      if (!Array.isArray(data)) return { bad: true };
      items = data;
    } else {
      raw.split(";").forEach((p) => { const i = p.indexOf("="); if (i > 0) items.push({ name: p.slice(0, i).trim(), value: p.slice(i + 1) }); });
    }
    const names = items.filter((c) => c && typeof c === "object" && c.name).map((c) => String(c.name));
    return names.length ? { count: names.length, session: names.includes("sessionid") } : { bad: true };
  }
  function renderCookieCheck() {
    const r = parseCookieText($("cookieInput").value);
    const box = $("cookieCheck");
    box.className = "cookie-check";
    $("btnSaveCookies").disabled = !(r && !r.bad);
    if (!r) { box.textContent = ""; return; }
    if (r.bad) { box.className += " bad"; box.textContent = t("ckBad"); }
    else if (r.session) { box.className += " ok"; box.textContent = tn("ckOk", r.count); }
    else { box.className += " warn"; box.textContent = tn("ckNoSession", r.count); }
  }
  $("cookieInput").addEventListener("input", renderCookieCheck);
  let manualTouched = false, lastCookieKind = null;
  $("manualCookie").querySelector("summary").addEventListener("click", () => { manualTouched = true; });

  $("btnSaveCookies").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      await apiA("/cookies", { method: "PUT", body: { raw: $("cookieInput").value } });
      $("cookieInput").value = "";
      renderCookieCheck();
      toast(t("toastCookieSaved"));
      await refresh();
    } catch (e) { $("cookieErr").textContent = e.message; }
  });
  $("btnClearCookies").addEventListener("click", async () => {
    if (!confirm(t("confirmClearCookies"))) return;
    try { await apiA("/cookies", { method: "DELETE" }); await refresh(); } catch (e) { toast(e.message); }
  });

  // ----------------------------------------------------------- remote login
  const view = $("remoteView");

  function renderLoginSteps() {
    const cls = loginMode === "idle" ? ["now", "", ""] : loginMode === "open" ? ["done", "now", ""] : ["done", "done", "now"];
    $("loginSteps").replaceChildren(...["step1", "step2", "step3"].map((k, i) =>
      el("li", { className: cls[i] }, [el("span", { className: "n", textContent: String(i + 1) }), t(k)])));
  }
  function renderLoginMsg() {
    const box = $("loginStateBox");
    const txt = loginMsg ? (loginMsg.raw || t(loginMsg.key, loginMsg.vars)) : "";
    setText("loginState", txt);
    box.classList.toggle("hidden", !txt);
    box.classList.toggle("warn", !!loginMsg && loginMsg.cls === "warn");
    box.classList.toggle("ok", !!loginMsg && loginMsg.cls === "ok");
  }
  function setLoginMsg(key, cls, vars) { loginMsg = key ? { key, vars, cls } : null; renderLoginMsg(); }

  function setLoginUi(active) {
    $("remoteCard").classList.toggle("hidden", !active);
    $("remoteWrap").classList.toggle("hidden", !active);
    $("btnLoginStart").classList.toggle("hidden", active);
    $("btnLoginSave").classList.toggle("hidden", !active);
    $("btnLoginStop").classList.toggle("hidden", !active);
  }

  let frameFails = 0;
  async function pullFrame() {
    if (framePending) return;
    framePending = true;
    try {
      const res = await fetch("/api/login/frame?t=" + Date.now(), { credentials: "same-origin" });
      if (res.status === 204) { if (loginMode !== "idle") endLogin("loginEnded"); return; }
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.status);
      const url = URL.createObjectURL(await res.blob());
      const old = view.src;
      view.src = url;
      if (old.startsWith("blob:")) URL.revokeObjectURL(old);
      frameFails = 0;
    } catch (e) {
      if (loginMode !== "idle" && ++frameFails >= 3) endLogin("loginEnded");
    } finally { framePending = false; }
  }

  let lastDiag = "";
  async function pullStatus() {
    try {
      const st2 = await api("/login/status");
      if (loginMode === "idle") return;
      if (!st2.active) return endLogin("loginEnded");
      loginMode = st2.logged_in ? "logged" : "open";
      renderLoginSteps();
      if (st2.logged_in) setLoginMsg("loginDetected", "ok"); else setLoginMsg("loginWaiting", "warn");
      setText("remoteUrl", st2.url || "-");
      const tabBtn = $("remTab");
      tabBtn.classList.toggle("hidden", !(st2.tabs > 1));
      tabBtn.textContent = t("remTabN", { i: st2.tab, n: st2.tabs });
      const diag = st2.diag || [];
      const sig = JSON.stringify(diag);
      if (sig !== lastDiag) {
        lastDiag = sig;
        $("remoteDiagBody").textContent = diag.length ? diag.map((d) => `[${d.t}] ${d.msg}`).join("\n") : t("diagEmpty");
        const info = [...diag].reverse().find((d) => d.kind === "dialog" || d.kind === "tab");
        $("remoteInfo").textContent = info ? info.msg : "";
        $("remoteInfo").classList.toggle("hidden", !info);
      }
    } catch (e) { /* diabaikan */ }
  }

  function endLogin(key, cls, vars) {
    clearInterval(loginTimer);
    loginTimer = null;
    loginMode = "idle";
    setLoginUi(false);
    renderLoginSteps();
    setLoginMsg(key, cls, vars);
  }

  $("btnLoginStart").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    setLoginMsg("loginOpening", "warn");
    try {
      await apiA("/login/start", { method: "POST" });
      loginMode = "open";
      setLoginUi(true);
      renderLoginSteps();
      setLoginMsg("loginWaiting", "warn");
      clearInterval(loginTimer);
      let n = 0;
      lastDiag = "";
      loginTimer = setInterval(() => { pullFrame(); if (++n % 3 === 0) pullStatus(); }, 700);
      pullFrame();
      pullStatus();
    } catch (e) { setLoginMsg(null); $("cookieErr").textContent = e.message; }
  });

  $("btnLoginStop").addEventListener("click", async () => {
    clearInterval(loginTimer);
    loginTimer = null;
    await api("/login/stop", { method: "POST" }).catch(() => {});
    endLogin("loginCancelled");
  });

  $("btnLoginSave").addEventListener("click", async () => {
    $("cookieErr").textContent = "";
    try {
      const r = await api("/login/save", { method: "POST" });
      endLogin("loginSaved", "ok", { n: r.saved });
      toast(t("toastLoginSaved"));
      await refresh();
    } catch (e) { $("cookieErr").textContent = e.message; }
  });

  function coords(ev) {
    const r = view.getBoundingClientRect();
    return { x: (ev.clientX - r.left) * view.naturalWidth / r.width, y: (ev.clientY - r.top) * view.naturalHeight / r.height };
  }
  // setelah klik/ketik langsung minta tampilan baru agar pengguna melihat reaksinya
  const send = (body, refreshNow = true) => api("/login/input", { method: "POST", body }).then(() => {
    if (!refreshNow) return;
    pullFrame();
    setTimeout(() => { pullFrame(); pullStatus(); }, 350);
  }).catch(() => {});
  let lastMove = 0;
  view.addEventListener("mousemove", (e) => {
    const now = Date.now();
    if (now - lastMove < 125) return;
    lastMove = now;
    send({ type: "move", ...coords(e) }, false);
  });
  $("remBack").addEventListener("click", () => send({ type: "nav", action: "back" }));
  $("remReload").addEventListener("click", () => send({ type: "nav", action: "reload" }));
  $("remLogin").addEventListener("click", () => send({ type: "nav", action: "login" }));
  $("remTab").addEventListener("click", () => send({ type: "nav", action: "tab" }));

  view.addEventListener("click", (e) => { view.focus(); send({ type: "click", ...coords(e) }); });
  view.addEventListener("wheel", (e) => {
    e.preventDefault();
    send({ type: "scroll", ...coords(e), dx: e.deltaX, dy: e.deltaY });
  }, { passive: false });
  view.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return; // biar paste lewat kolom teks
    if (e.key.length === 1 || ["Backspace", "Tab", "Enter", "Escape", "Delete", "Home", "End", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
      e.preventDefault();
      send({ type: "key", key: e.key });
    }
  });
  view.addEventListener("paste", (e) => {
    e.preventDefault();
    send({ type: "text", text: e.clipboardData.getData("text") });
  });
  $("remoteText").addEventListener("keydown", async (e) => {
    if (e.key !== "Enter") return;
    const v = e.target.value;
    e.target.value = "";
    if (v) await send({ type: "text", text: v });
  });

  // ------------------------------------------------------- schedules editor
  const options = (n, val, label) => {
    const sel = el("select", { "aria-label": label });
    for (let i = 0; i < n; i++) sel.append(new Option(pad(i), pad(i)));
    sel.value = val;
    return sel;
  };

  function addScheduleRow(sc = { id: "", enabled: true, time: "07:00", message: "", contacts: null }) {
    const [hh, mm] = sc.time.split(":");
    const enabled = el("input", { type: "checkbox", className: "switch", checked: sc.enabled, role: "switch", "aria-label": t("schedEnabled") });
    const hour = options(24, hh, t("hour")), min = options(60, mm, t("minute"));
    const title = el("div", { className: "title" });
    const meta = el("div", { className: "meta" });
    const del = el("button", { className: "more-btn", type: "button", "aria-haspopup": "menu", "aria-expanded": "false" }, [icon("i-more")]);
    const hint = el("p", { className: "busy-hint hidden", role: "status" }, [icon("i-warn"), el("span", { textContent: t("busyHint") })]);
    const msg = el("input", { type: "text", value: sc.message || "", placeholder: t("schedMsgPh"), maxLength: 500, "aria-label": t("schedMsgPh") });

    // Penerima: semua kontak akun, atau hanya yang dicentang
    const allBox = el("input", { type: "checkbox", className: "switch", checked: sc.contacts == null, role: "switch" });
    const chips = el("div", { className: "chips" });
    const selected = new Set((sc.contacts || []).map((c) => c.toLowerCase()));
    const head = () => {
      title.textContent = partName(+hour.value);
      meta.textContent = allBox.checked ? t("allContacts", { n: contactList.length })
        : tn("nContacts", contactList.filter((c) => selected.has(c.toLowerCase())).length);
      del.setAttribute("aria-label", `${t("moreActions")}: ${hour.value}:${min.value}`);
    };
    const buildChips = () => {
      chips.replaceChildren();
      contactList.forEach((c) => {
        const key = c.toLowerCase();
        const cb = el("input", { type: "checkbox", checked: selected.has(key) });
        cb.addEventListener("change", () => { if (cb.checked) selected.add(key); else selected.delete(key); head(); });
        chips.append(el("label", { className: "chip" }, [cb, icon("i-check", "tick"), el("span", { textContent: c })]));
      });
      if (!contactList.length) chips.append(el("span", { className: "muted", textContent: t("noContactsHere") }));
      chips.classList.toggle("hidden", allBox.checked);
      head();
    };
    allBox.addEventListener("change", buildChips);
    hour.addEventListener("change", head);
    min.addEventListener("change", head);
    buildChips();

    const row = el("div", { className: "sched" + (sc.enabled ? "" : " off") }, [
      el("div", { className: "sched-top" }, [
        enabled,
        el("div", { className: "time-pick" }, [hour, el("span", { textContent: ":" }), min]),
        el("div", { className: "grow" }, [title, meta]),
        del,
      ]),
      msg,
      el("label", { className: "switch-row" }, [el("span", { textContent: t("sendToAll") }), allBox]),
      chips,
      hint,
    ]);
    row.setContacts = buildChips;
    row.updateHint = () => {
      const n = slotInfo && slotInfo.slots ? slotInfo.slots[slotKey(hour.value, min.value)] || 0 : 0;
      // hitungan sudah memuat jadwal ini sendiri bila tersimpan di jam yang sama; ambang "ramai" diukur di atasnya
      hint.classList.toggle("hidden", !(slotInfo && enabled.checked && n >= slotInfo.busy_at));
    };
    hour.addEventListener("change", row.updateHint);
    min.addEventListener("change", row.updateHint);
    enabled.addEventListener("change", row.updateHint);
    row.updateHint();
    row.dataset.id = sc.id || "";
    enabled.addEventListener("change", () => row.classList.toggle("off", !enabled.checked));
    del.addEventListener("click", () => openMenu(del, [
      { label: t("delSchedule"), icon: "i-trash", danger: true, onClick: () => { row.remove(); syncSchedEmpty(); } },
    ], t("moreActions")));
    row.read = () => ({
      id: row.dataset.id || null,
      enabled: enabled.checked,
      time: `${hour.value}:${min.value}`,
      message: msg.value.trim(),
      contacts: allBox.checked ? null : contactList.filter((c) => selected.has(c.toLowerCase())),
    });
    $("scheduleList").append(row);
  }

  function syncSchedEmpty() {
    const box = $("scheduleList");
    const empty = box.querySelector(".empty");
    const has = box.querySelector(".sched");
    if (!has && !empty) box.append(el("p", { className: "empty", textContent: t("noScheds") }));
    else if (has && empty) empty.remove();
  }

  function renderSchedules(list) {
    $("scheduleList").replaceChildren();
    [...list].sort((x, y) => x.time.localeCompare(y.time)).forEach(addScheduleRow);
    syncSchedEmpty();
  }
  const readSchedules = () => [...$("scheduleList").querySelectorAll(".sched")].map((r) => r.read());

  $("btnAddSchedule").addEventListener("click", () => {
    if ($("scheduleList").querySelectorAll(".sched").length >= 8) return toast(t("maxSchedules"));
    $("scheduleList").querySelector(".empty")?.remove();
    addScheduleRow();
  });

  $("btnSaveSchedules").addEventListener("click", async () => {
    try {
      const acc = await api("/accounts/" + currentId, { method: "PUT", body: { schedules: readSchedules() } });
      renderSchedules(acc.schedules);
      setMsg("scheduleMsg", "", "schedulesSaveHint");
      loadSlots();
      toast(t("toastSchedulesSaved"));
      await refresh();
    } catch (e) { setMsg("scheduleMsg", e.message); }
  });

  // --------------------------------------------------------------- settings
  async function loadSettings() {
    const s0 = await api("/settings");
    settings = s0;
    $("setMessage").value = s0.message;
    $("setTimezone").value = s0.timezone;
    $("setNotifyShot").checked = s0.notify_screenshot;
    $("setKeepalive").checked = s0.keepalive_enabled;
    $("setKeepaliveHours").value = s0.keepalive_hours;
    $("setPageWait").value = s0.page_load_wait;
    $("setElementWait").value = s0.element_wait;
    $("setSendDelay").value = s0.send_delay;
    $("setTgEnabled").checked = s0.telegram_enabled;
    $("setTgChat").value = s0.telegram_chat_id;
    $("setTgToken").value = "";
    $("setDcEnabled").checked = s0.discord_enabled;
    $("setDcWebhook").value = "";
    renderSettingsStates();
    renderDashboard();
  }
  function renderSettingsStates() {
    if (!settings) return;
    setText("dcWebhookState", settings.discord_webhook_set ? t("saved") : "");
    setText("tgTokenState", settings.telegram_token_set ? t("saved") : "");
    $("tzLabel").textContent = t("tzLabel", { tz: settings.timezone || t("tzServer") });
    setText("nrChannels", globalChannelNames());
    setText("nrMessage", settings.timezone);
    setText("nrCookie", settings.keepalive_enabled ? tn("refreshEvery", settings.keepalive_hours) : t("refreshOff"));
    setText("nrWaits", `${settings.page_load_wait} · ${settings.element_wait} · ${t("secUnit", { s: settings.send_delay })}`);
  }

  // sheet pengaturan global (satu panel per kelompok)
  const PANEL_TITLE = { channels: "gChannels", message: "gMessage", cookie: "cookieRefresh", waits: "gWaits" };
  let setTrigger = null;
  function openSetSheet(panel, trigger) {
    setTrigger = trigger;
    closeMenu(false);
    document.querySelectorAll(".set-panel").forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== panel));
    $("settingsForm").dataset.panel = panel;
    setText("setSheetTitle", t(PANEL_TITLE[panel]));
    setText("settingsMsg", "");
    $("setSheet").classList.remove("hidden");
    document.body.style.overflow = "hidden";
    const first = document.querySelector(`.set-panel[data-panel="${panel}"] input`);
    if (first) first.focus();
  }
  function closeSetSheet(silent) {
    if ($("setSheet").classList.contains("hidden")) return;
    $("setSheet").classList.add("hidden");
    document.body.style.overflow = "";
    if (!silent && setTrigger) setTrigger.focus();
  }
  document.querySelectorAll(".nav-row[data-panel]").forEach((b) => b.addEventListener("click", () => openSetSheet(b.dataset.panel, b)));
  $("setCancel").addEventListener("click", () => closeSetSheet());
  $("setSheet").addEventListener("mousedown", (e) => { if (e.target === $("setSheet")) closeSetSheet(); });

  const panelBody = (panel) => ({
    channels: () => ({
      notify_screenshot: $("setNotifyShot").checked,
      discord_enabled: $("setDcEnabled").checked, discord_webhook: $("setDcWebhook").value.trim(),
      telegram_enabled: $("setTgEnabled").checked, telegram_token: $("setTgToken").value.trim(), telegram_chat_id: $("setTgChat").value.trim(),
    }),
    message: () => ({ message: $("setMessage").value, timezone: $("setTimezone").value.trim() === (settings && settings.timezone_default) ? "" : $("setTimezone").value.trim() }),
    cookie: () => ({ keepalive_enabled: $("setKeepalive").checked, keepalive_hours: +$("setKeepaliveHours").value }),
    waits: () => ({ page_load_wait: +$("setPageWait").value, element_wait: +$("setElementWait").value, send_delay: +$("setSendDelay").value }),
  })[panel]();
  async function saveGlobal(body) { await api("/settings", { method: "PUT", body }); await loadSettings(); }

  $("settingsForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await saveGlobal(panelBody($("settingsForm").dataset.panel));
      toast(t("toastSettingsSaved"));
      closeSetSheet();
      await refresh();
    } catch (err) { setText("settingsMsg", err.message); }
  });
  const testHook = (path, save) => async () => {
    try { if (save) await save(); await api(path, { method: "POST" }); toast(t("toastTestSent")); }
    catch (e) { toast(e.message); }
  };
  $("btnDcTest").addEventListener("click", testHook("/discord/test", () => saveGlobal(panelBody("channels"))));
  $("btnTgTest").addEventListener("click", testHook("/telegram/test", () => saveGlobal(panelBody("channels"))));

  // ------------------------------------------------- notifikasi pribadi
  function syncMyFields() {
    $("myDcFields").classList.toggle("hidden", !$("myDcEnabled").checked);
    $("myTgFields").classList.toggle("hidden", !$("myTgEnabled").checked);
  }
  $("myDcEnabled").addEventListener("change", syncMyFields);
  $("myTgEnabled").addEventListener("change", syncMyFields);
  async function loadMyNotif() {
    myNotif = await api("/me/notifications");
    $("myDcEnabled").checked = myNotif.discord_enabled;
    $("myTgEnabled").checked = myNotif.telegram_enabled;
    $("myTgChat").value = myNotif.telegram_chat_id;
    $("myShot").checked = myNotif.notify_screenshot;
    $("myDcWebhook").value = "";
    $("myTgToken").value = "";
    syncMyFields();
    renderMyNotifStates();
    renderDashboard();
  }
  function renderMyNotifStates() {
    if (!myNotif) return;
    setText("myDcState", myNotif.discord_webhook_set ? "· " + t("saved") : "");
    setText("myTgState", myNotif.telegram_token_set ? "· " + t("saved") : "");
  }
  async function saveMyNotif() {
    await api("/me/notifications", { method: "PUT", body: {
      discord_enabled: $("myDcEnabled").checked,
      discord_webhook: $("myDcWebhook").value.trim(),
      telegram_enabled: $("myTgEnabled").checked,
      telegram_token: $("myTgToken").value.trim(),
      telegram_chat_id: $("myTgChat").value.trim(),
      notify_screenshot: $("myShot").checked,
    } });
    await loadMyNotif();
  }
  $("myNotifForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try { await saveMyNotif(); setText("myNotifMsg", ""); toast(t("toastNotifSaved")); }
    catch (err) { setText("myNotifMsg", err.message); }
  });
  $("btnMyTest").addEventListener("click", async () => {
    if (!$("myDcEnabled").checked && !$("myTgEnabled").checked) { toast(t("enableTgDcFirst")); return; }
    try {
      await saveMyNotif();
      if (myNotif.discord_enabled) await api("/me/notifications/test/discord", { method: "POST" });
      if (myNotif.telegram_enabled) await api("/me/notifications/test/telegram", { method: "POST" });
      toast(t("toastTestSent"));
    } catch (e) { toast(e.message); }
  });
  $("rowChangePw").addEventListener("click", openPwModal);
  $("rowLogout").addEventListener("click", logout);

  // ------------------------------------------------------ kelola pengguna
  let newRole = "user";
  document.querySelectorAll("#newUserRole [data-role]").forEach((b) => b.addEventListener("click", () => {
    newRole = b.dataset.role;
    document.querySelectorAll("#newUserRole [data-role]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  }));
  async function userAction(u, body, doneKey) {
    try { await api("/users/" + u.id, { method: "PUT", body }); toast(t(doneKey || "toastUserUpdated")); await loadUsers(); }
    catch (e) { toast(e.message); }
  }
  function renderUsers() {
    const box = $("userList");
    box.replaceChildren();
    setText("usersCount", String(users.length));
    users.forEach((u) => {
      const self = me && u.id === me.id;
      const more = el("button", { className: "more-btn", type: "button", "aria-haspopup": "menu", "aria-expanded": "false", "aria-label": `${t("moreActions")}: ${u.username}` }, [icon("i-more")]);
      more.addEventListener("click", () => openMenu(more, [
        { label: t("resetPw"), icon: "i-key", onClick: () => {
          const pw = prompt(t("promptNewPw", { name: u.username }));
          if (pw) userAction(u, { password: pw });
        } },
        { label: t(u.role === "admin" ? "makeUser" : "makeAdmin"), icon: "i-shield", disabled: self, reason: self ? t("yourself") : "", onClick: () => userAction(u, { role: u.role === "admin" ? "user" : "admin" }) },
        { label: t(u.disabled ? "enable" : "disable"), icon: "i-ban", disabled: self, reason: self ? t("yourself") : "", onClick: () => {
          if (u.disabled || confirm(t("confirmDisable", { name: u.username }))) userAction(u, { disabled: !u.disabled });
        } },
        { sep: true },
        { label: t("delUser"), icon: "i-trash", danger: true, disabled: self, reason: self ? t("yourself") : "", onClick: async () => {
          if (!confirm(t("confirmDeleteUser", { name: u.username, n: u.accounts }))) return;
          try { await api("/users/" + u.id, { method: "DELETE" }); toast(t("toastUserDeleted")); await loadUsers(); await refresh(); }
          catch (e) { toast(e.message); }
        } },
      ], u.username));
      const line = el("div", { className: "title-line" }, [el("span", { className: "title", textContent: u.username }),
        el("span", { className: "badge " + (u.role === "admin" ? "accent" : "neutral"), textContent: t(u.role === "admin" ? "roleAdmin" : "roleUser") })]);
      const n = tn("acctCount", u.accounts);
      const meta = self ? t("userMetaSelf", { n }) : t("userMeta", { n, state: t(u.disabled ? "stateDisabled" : "stateActive") });
      box.append(el("div", {}, [
        paint(el("span", { className: "avatar-sm", textContent: initial(u.username), "aria-hidden": "true" }), u.id),
        el("div", { className: "grow" }, [line, el("div", { className: "meta line", textContent: meta })]),
        more,
      ]));
    });
  }
  $("btnAddUser").addEventListener("click", async () => {
    $("userErr").textContent = "";
    try {
      await api("/users", { method: "POST", body: { username: $("newUserName").value, password: $("newUserPass").value, role: newRole } });
      $("newUserName").value = $("newUserPass").value = "";
      toast(t("toastUserAdded"));
      await loadUsers();
    } catch (e) { $("userErr").textContent = e.message; }
  });

  // ----------------------------------------------------------- render semua
  function renderAll() {
    renderLoginSteps();
    renderLoginMsg();
    if (!accounts.length) return;
    dashSig = "";
    renderAccountList(true);
    renderDashboard(true);
    renderQueue(true);
    renderHistFilters();
    renderHistory();
    renderQueueAdmin();
    renderContacts(contactList);
    renderSettingsStates();
    renderMyNotifStates();
    renderCookieCheck();
    renderUsers();
    syncMyFields();
    if (me) applyRole();
    updateEyes();
    const b = $("runBadge");
    if (b.dataset.status) b.textContent = statusLabel(b.dataset.status);
    idleLogKey = null;
    renderIdleLog();
    if (lb.open) showLightboxItem();
    renderShotButtons();
    $("shotView").title = t("fullScreen");
    if (!$("app").classList.contains("hidden")) renderSchedules(readSchedules());
  }

  // ------------------------------------------------------------------ start
  document.documentElement.lang = lang;
  document.querySelectorAll(".segmented [data-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
  applyStaticI18n();
  applyTheme(theme);
  $("loginLangCode").textContent = lang.toUpperCase();
  $("loginLang").setAttribute("aria-label", `${t("language")}: ${lang.toUpperCase()}`);
  $("loginLang").title = $("loginLang").getAttribute("aria-label");
  updateEyes();
  renderShotButtons();
  renderLoginSteps();
  renderLoginMsg();
  renderHistFilters();
  showTab("dashboard");
  initAuth();
})();
