// https://serverfault.com/a/841150
// https://github.com/systemd/systemd/commit/88ced61bf9673407f4b15bf51b1b408fd78c149d

// Allow certbot to manage nginx.service;
// fall back to implicit authorization otherwise.
polkit.addRule(function(action, subject) {
  if (action.id == "org.freedesktop.systemd1.manage-units" &&
      action.lookup("unit") == "nginx.service" &&
      action.lookup("verb") == "reload" &&
      subject.user == "certbot") {
      return polkit.Result.YES;
  }
});
