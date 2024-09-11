from distutils.core import setup
import setup_translate

pkg = 'Extensions.ShootYourScreen'
setup(name='enigma2-plugin-extensions-shootyourscreen',
	version='0.3',
	description='make Screenshots with your E2',
	packages=[pkg],
	package_dir={pkg: 'plugin'},
	package_data={pkg: ['locale/*/LC_MESSAGES/*.mo', 'shootyourscreen.png']},
	cmdclass=setup_translate.cmdclass, # for translation
)
