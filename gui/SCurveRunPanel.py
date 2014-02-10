# Pyjamas panel to take an s-curve run.
#
# @author Mark Grimes (mark.grimes@bristol.ac.uk)
# @date 17/Jan/2014

from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.FlowPanel import FlowPanel
from pyjamas.ui.DisclosurePanel import DisclosurePanel
from pyjamas.ui.ListBox import ListBox
from pyjamas.ui.Label import Label
from pyjamas.ui.TextBox import TextBox
from pyjamas.ui.Button import Button

from pyjamas.ui.Image import Image

from pyjamas.Canvas.GWTCanvas import GWTCanvas as Canvas
from pyjamas.ui.Composite import Composite
from pyjamas.Canvas import Color
#from pyjamas.Canvas.SVGCanvas import SVGCanvas as Canvas
from pyjamas.Canvas.ImageLoader import loadImages

from ErrorMessage import ErrorMessage
from GlibRPCService import GlibRPCService
from DataRunManager import DataRunManager
from DisplayHistogramsPanel import DisplayHistogramsPanel

class SCurveRunPanel :
	
	class onClickListener :
		def __init__(self, panel) :
			self._ClickPanel=panel	
			
		def onRemoteResponse(self, response, request_info):
			pass
			
		def onRemoteError(self, code, message, request_info):
			ErrorMessage( "Unable to contact server" )

	class loadImageListener:
		def __init__(self, panel) :
			self._loadImagePanel=panel	
			
		def onRemoteResponse(self, response, request_info):
			self._loadImagePanel.image=response
			
		def onRemoteError(self, code, message, request_info):
			ErrorMessage( "Unable to contact server" )
			
	class controlSCurveValueListener :
		def __init__(self, panel) :
			self._controlPanel=panel
			#self._controlPanel.launchButton.setEnabled(False)
			#self._controlPanel.echoSelection()
			
		def onRemoteResponse(self, response, request_info):
			self._controlPanel.launchButton.setEnabled(False)
			
		def onRemoteError(self, code, message, request_info):
			ErrorMessage( "Unable to contact server" )

	class DoNothingListener :
		"""
		A class to listen for the response to any calls where I don't care about the result.
		Later on I'll put in a popup if there's a message.
		"""
		def onRemoteResponse(self, response, request_info):
			# Don't actually want to do anything
			ErrorMessage( "Unable to contact server: "+str(response) )
			pass

		def onRemoteError(self, code, message, request_info):
			ErrorMessage( "Unable to contact server: "+str(message) )

	class DataTakingStatusListener :
		def __init__( self, SCurveRunPanelInstance ) :
			self.parentInstance=SCurveRunPanelInstance
		def onRemoteResponse(self, response, request_info):
			self.parentInstance.echo.setText(response["statusString"] )
			if response["fractionComplete"]<1:
				self.parentInstance.launchButton.setEnabled(False)
			else:
				self.parentInstance.launchButton.setEnabled(True)
				self.parentInstance.echo.setText("No data taking")
		def onRemoteError(self, code, message, request_info):
			ErrorMessage( "Unable to contact server: "+str(message) )

	
	def __init__( self ) :
		# This is the service that will be used to communicate with the DAQ software
		self.rpcService = GlibRPCService.instance()
		self.dataRunManager = DataRunManager.instance()

		self.mainPanel = VerticalPanel()
		self.mainPanel.setSpacing(15)
		
		self.controlValueEntries={} #controls the parameters of the s-curve
		
		self.mainSettings=VerticalPanel("Control Settings")
		self.startButton=VerticalPanel("Run Button")
		self.canvasPanel=VerticalPanel("Canvas")
		
		self.mainSettings.add(self.createControlPanel(["RangeLo","RangeHi","Steps","FileName"]))
		
		self.echo=Label() # A good print screen method
		
		self.launchButton=Button("Launch Now")
		self.launchButton.addClickListener(self)
		self.launchButton.setEnabled(True)
		
		self.mainPanel.add(self.mainSettings)
		self.mainPanel.add(self.startButton)
		self.mainPanel.add(self.launchButton)
		self.mainPanel.add(self.echo)
		histogramDisplay=DisplayHistogramsPanel()
		self.mainPanel.add( HTML( '<br><b>Results:</b> (note that selecting a lot of channels can take a very long time)') )
		self.mainPanel.add( histogramDisplay.getPanel() )
		
		self.dataRunManager.registerEventHandler( self )
		
		self.imageTimer = Timer(notify=self.updateImage)
		self.imageTimer.scheduleRepeating(5000)

		
		self.image=Image("images/Three_Colours-Blue-Coffee-Sugar.jpg")

		
		self.mainPanel.add(self.image)
		

	def onDataTakingEvent( self, eventCode, details ) :
		"""
		Method that receives updates from DataRunManager
		"""
		if eventCode==DataRunManager.DataTakingStartedEvent :
			self.echo.setText("Taking data... ")
			self.launchButton.setEnabled(False)
		elif eventCode==DataRunManager.DataTakingFinishedEvent :
			self.echo.setText("Data taking finished")
			self.launchButton.setEnabled(True)
		elif eventCode==DataRunManager.DataTakingStatusEvent :
			self.echo.setText("%3d%% - "%int(details['fractionComplete']*100+0.5)+details['statusString'] )
			
	def onChange( self, sender ) :
		pass
		
	def onClick(self, sender):
		
		if sender==self.launchButton :
			self.echo.setText("Initiating run")
			rangeHigh=int(self.rangeHighBox.getText())
			rangeLow=int(self.rangeLowBox.getText())
			stepSize=int(self.stepSizeBox.getText())
			self.dataRunManager.startSCurveRun( range(rangeLow,rangeHigh,stepSize) )	
			
	def updateStatus(self):
		self.rpcService.getDataTakingStatus( None, SCurveRunPanel.DataTakingStatusListener(self) )

	def updateImage(self):
		self.mainPanel.remove(self.image)
		self.image=Image("images/Three_Colours-Blue-Coffee-Sugar.jpg")
		self.mainPanel.add(self.image)
	
	def getPanel(self) :
		return self.mainPanel
        
	def createControlPanel(self, controlNames):
		flowPanel=FlowPanel()
		newLabels=[]
		for buttonName in controlNames:
			newPanel=HorizontalPanel()
			newLabels.append(Label(buttonName))
			newPanel.add(newLabels[-1])
			newTextBox=TextBox()
			newTextBox.setEnabled(True)
			newTextBox.setWidth(80)
			newPanel.add(newTextBox)	
			if buttonName=="RangeLo" :
				newTextBox.setText("100") # Default values
				self.rangeLowBox=newTextBox
			elif buttonName=="RangeHi" :
				newTextBox.setText("150")
				self.rangeHighBox=newTextBox
			elif buttonName=="Steps" :
				newTextBox.setText("1")
				self.stepSizeBox=newTextBox
			elif buttonName=="FileName": newTextBox.setText("TestRun.png")
			
			#newTextBox.addChangeListener(self)
			newTextBox.setTitle(buttonName)
			
			self.controlValueEntries[buttonName]=newTextBox	
			
			flowPanel.add(newPanel)
		

		# Set all of the widths of the labels to be the same, so that the boxes line up
		maxWidth=0
		for label in newLabels :
			# This doesn't work for some reason
			#if label.getWidth() > maxWidth : maxWidth=label.getWidth()
			if len(label.getText())*9 > maxWidth : maxWidth=len(label.getText())*9
		for label in newLabels :
			label.setWidth(maxWidth)

		return flowPanel


