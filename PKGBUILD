# Maintainer: Syreese <syreeseofficial@gmail.com>
pkgname=hypertyper
_pkgname=HyperTyper
pkgver=1.0.2
pkgrel=1
pkgdesc="A CLI Typing Game with multiple modes, streaks, and sound effects"
arch=('any')
url="https://github.com/SyreeseOfficial/HyperTyper"
license=('MIT')
depends=('python' 'python-pygame' 'python-colorama')
makedepends=()
source=("${url}/archive/v${pkgver}.tar.gz")
sha256sums=('629e692410ba9075e66010e1a9da042d74c63a2963e4f57e2f0763ab03bd3048')

package() {
    # GitHub archive usually extracts to RepoName-Tag
    cd "${_pkgname}-${pkgver}" || cd "${pkgname}-${pkgver}" || return 1
    
    # Install the main executable
    install -Dm755 hypertyper.py "$pkgdir/usr/bin/$pkgname"
    
    # Install data files to /usr/share/hypertyper/data
    mkdir -p "$pkgdir/usr/share/$pkgname/data"
    cp -r data/* "$pkgdir/usr/share/$pkgname/data/"
}
